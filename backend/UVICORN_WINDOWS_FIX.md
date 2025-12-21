# 🔧 Fix KeyboardInterrupt sur Windows avec uvicorn --reload

## Problème

Sur Windows, uvicorn avec `--reload` affiche parfois cette erreur lors du rechargement :
```
KeyboardInterrupt
File "<frozen codecs>", line 312, in __init__
```

## ✅ Solution : Ce n'est PAS une erreur bloquante

Cette erreur est **cosmétique** et n'empêche pas le serveur de fonctionner. Le rechargement fonctionne quand même.

## Options pour réduire l'erreur

### Option 1: Utiliser --reload-dir (Recommandé)

Limitez les fichiers surveillés pour réduire les rechargements :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-dir app
```

### Option 2: Désactiver le rechargement automatique

Si l'erreur vous dérange, lancez sans `--reload` et redémarrez manuellement :

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Option 3: Utiliser watchfiles (plus stable)

Installez watchfiles qui est plus stable sur Windows :

```bash
pip install watchfiles
```

Puis utilisez :

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --reload-engine watchfiles
```

### Option 4: Utiliser un autre serveur de dev

Utilisez `fastapi dev` (si disponible) ou un autre outil :

```bash
fastapi dev app.main:app
```

## Vérification

Pour vérifier que tout fonctionne malgré l'erreur :

1. Le serveur répond toujours : `curl http://localhost:8000/api/health`
2. Les changements sont rechargés (testez en modifiant un fichier)
3. Les logs continuent de s'afficher

## Conclusion

**Vous pouvez ignorer cette erreur** - elle n'affecte pas le fonctionnement de l'application. Le serveur continue de tourner et le hot-reload fonctionne.

