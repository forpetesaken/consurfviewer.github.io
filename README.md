# ConSurf Interactive Viewer Site

This folder is a ready-to-publish static website and can be used as its own git repo.
It includes top tabs for:

- RAD21
- STAG1
- STAG2
- CTCF

## Files

- `index.html` - interactive ConSurf viewer (standalone, works without internet once loaded)
- `build_site.py` - builds the site from latest ConSurf `.grades` files
- `update_viewer.ps1` - rebuilds `index.html` from the latest RAD21 ConSurf grade outputs

## Keep Site Updated

Run this from inside this folder whenever new ConSurf outputs are generated:

```powershell
.\update_viewer.ps1
```

This rebuilds tabs/datasets from current files under `ConSurf/output/`.

Then commit and push:

```powershell
git add index.html
git commit -m "Update viewer data"
git push
```

## Quick publish options

### Option 1: GitHub Pages

1. Create a new GitHub repository.
2. Upload the contents of this folder (`index.html`).
3. In repository settings, open **Pages**.
4. Set source to **Deploy from a branch** and choose `main` + `/ (root)`.
5. Save. GitHub will provide a public URL.

### Option 2: Netlify (drag and drop)

1. Go to Netlify Drop: https://app.netlify.com/drop
2. Drag this `consurf_viewer_site` folder into the page.
3. Netlify gives you a public share link immediately.

### Option 3: Share as a single file

You can also share just `index.html` directly. People can open it in a browser.
