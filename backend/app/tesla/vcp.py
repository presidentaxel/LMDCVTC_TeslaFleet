from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import websockets
from pydantic import BaseModel

from app.core.settings import settings

import logging

logger = logging.getLogger(__name__)

class VCPError(RuntimeError):
    pass


class CommandStatus(BaseModel):
    success: bool
    error: Optional[str] = None
    raw: Dict[str, Any]


@dataclass
class VehicleCommandProtocol:
    access_token: str
    region: str = settings.TESLA_REGION.lower()

    def _ws_url(self) -> str:
        base = settings.tesla_audience_for(self.region)
        # Base looks like https://fleet-api.prd.eu.vn.cloud.tesla.com
        return base.replace("https://", "wss://").rstrip("/") + "/vehicle-commands"

    async def _connect(self, vehicle_id: str):
        safe_vehicle = str(vehicle_id)[-6:]
        logger.debug(
            "Opening VCP websocket (region=%s, vehicle_suffix=%s)",
            self.region,
            safe_vehicle,
        )
        headers = [
            ("Authorization", f"Bearer {self.access_token}"),
            ("Tesla-Account-Type", "Fleet"),
            ("Tesla-Vehicle-Command-Protocol-Version", "1"),
            ("Tesla-Client-Request-Id", str(uuid.uuid4())),
            ("Tesla-Client-App-Source", "fleet_api"),
            ("Tesla-App-Platform", "web"),
            ("Tesla-App-Version", "1.0.0"),
            ("User-Agent", "tesla-fleet-proxy/1.0"),
            ("Tesla-User-Agent", "tesla-fleet-proxy/1.0"),
        ]
        url = f"{self._ws_url()}?vehicle_id={vehicle_id}"
        return await websockets.connect(
            url,
            additional_headers=headers,
            subprotocols=["vcp"],
            max_size=2 * 1024 * 1024,
            ping_interval=None,
        )

    async def execute(
        self,
        vehicle_id: str,
        command_name: str,
        command_params: Optional[Dict[str, Any]] = None,
        *,
        timeout: float = 20.0,
    ) -> CommandStatus:
        command_params = command_params or {}
        try:
            async with await self._connect(vehicle_id) as ws:
                connection_info = await asyncio.wait_for(ws.recv(), timeout=timeout)
                info = json.loads(connection_info)
                if info.get("message_type") != "connection_info":
                    raise VCPError(f"Unexpected first message: {info}")
                connection_id = info.get("connection_info", {}).get("connection_id")
                if not connection_id:
                    raise VCPError("Missing connection_id in connection_info")
                logger.debug(
                    "VCP connection established (region=%s, vehicle_suffix=%s, connection_id=%s)",
                    self.region,
                    str(vehicle_id)[-6:],
                    connection_id,
                )

                request_id = str(uuid.uuid4())
                message_id = str(uuid.uuid4())
                payload = {
                    "message_type": "command_request",
                    "message_id": message_id,
                    "command_request": {
                        "request_id": request_id,
                        "connection_id": connection_id,
                        "command_name": command_name,
                        "command_params": command_params,
                        "deliver_to_vehicle": True,
                        "response_required": True,
                        "vehicle_id": str(vehicle_id),
                    },
                }
                await ws.send(json.dumps(payload))

                while True:
                    raw_msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                    data = json.loads(raw_msg)
                    msg_type = data.get("message_type")

                    if msg_type == "command_response":
                        cmd_resp = data.get("command_response", {})
                        status = cmd_resp.get("status") or cmd_resp.get("result")
                        success = (status or "").lower() in {"success", "succeeded", "ok"}
                        error = None if success else cmd_resp.get("error") or status
                        logger.debug(
                            "VCP command_response (region=%s, vehicle_suffix=%s, success=%s, status=%s)",
                            self.region,
                            str(vehicle_id)[-6:],
                            success,
                            status,
                        )
                        return CommandStatus(success=success, error=error, raw=data)

                    if msg_type == "command_status":
                        # Interim status update; continue to wait
                        logger.debug(
                            "VCP command_status update (region=%s, vehicle_suffix=%s, payload=%s)",
                            self.region,
                            str(vehicle_id)[-6:],
                            cmd_resp if (cmd_resp := data.get("command_status")) else {},
                        )
                        continue

                    if msg_type == "error":
                        err = data.get("error", {}).get("message") or "Unknown VCP error"
                        raise VCPError(err)

        except asyncio.TimeoutError as exc:
            raise VCPError("Vehicle command timed out") from exc
        except websockets.InvalidStatusCode as exc:
            logger.error(
                "VCP handshake failed (region=%s, vehicle_suffix=%s, status=%s)",
                self.region,
                str(vehicle_id)[-6:],
                getattr(exc, "status_code", "?"),
            )
            raise VCPError(f"WebSocket handshake failed: HTTP {getattr(exc, 'status_code', '?')}") from exc
        except websockets.WebSocketException as exc:
            logger.error(
                "VCP websocket error (region=%s, vehicle_suffix=%s): %s",
                self.region,
                str(vehicle_id)[-6:],
                exc,
            )
            raise VCPError(f"WebSocket error: {exc}") from exc

        raise VCPError("No command response received")

