# Tesla Fleet Public Key Site

This tiny static site only serves the Tesla Fleet OAuth public key under
`.well-known/appspecific/com.tesla.3p.public-key.pem`. Deploy it to Vercel so
Tesla can fetch the key when registering your partner application.

## Steps

1. Rename `public/.well-known/appspecific/com.tesla.3p.public-key.pem.example`
   to `com.tesla.3p.public-key.pem` and replace the placeholder with your real
   Tesla PEM.
2. Commit and push.
3. Create a Vercel project linked to this folder, set the framework to
   “Other” (static site), build command empty, output directory `public`.
4. Add the domain `public-key-site.vercel.app` (or your custom domain).
5. Visit
   `https://public-key-site.vercel.app/.well-known/appspecific/com.tesla.3p.public-key.pem`
   to confirm Tesla can reach the file.

