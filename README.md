# Owen Heap — Data Science Portfolio

Built with [Quarto](https://quarto.org) and deployed to GitHub Pages.

---

## 🚀 Getting Started (Step-by-Step)

### Step 1 — Install Quarto
Download and install Quarto from https://quarto.org/docs/get-started/
(It works natively with RStudio — no extra setup needed after installing.)

### Step 2 — Open in RStudio
1. Unzip this folder somewhere you want to keep it (e.g. `Documents/owen-heap-portfolio`)
2. Double-click `owen-heap-portfolio.Rproj` to open in RStudio
3. In the RStudio terminal (not console), run:
   ```
   quarto preview
   ```
   Your site will open in your browser at `localhost:4242` with live reload. ✅

### Step 3 — Push to GitHub
1. Create a **new empty repository** on GitHub named `owen-heap-portfolio`
   - Do NOT initialize with README or .gitignore (the folder already has these)
2. In RStudio Terminal, run these commands one at a time:
   ```
   git init
   git add .
   git commit -m "Initial portfolio"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/owen-heap-portfolio.git
   git push -u origin main
   ```
   *(Replace YOUR_USERNAME with your GitHub username)*

### Step 4 — Enable GitHub Pages
1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Source**, select: **Deploy from a branch**
3. Branch: `gh-pages` / folder: `/ (root)` → **Save**
4. Wait ~2 minutes. Your site will be live at:
   `https://YOUR_USERNAME.github.io/owen-heap-portfolio`

> **Note:** After the first push, GitHub Actions will automatically build and deploy
> every time you push new changes. You never need to manually render.

---

## ✏️ Customizing Your Site

| File | What to edit |
|------|-------------|
| `index.qmd` | Home page — update hero text, project cards, skills |
| `about.qmd` | Your bio, background, contact info |
| `projects.qmd` | Project descriptions and links |
| `posts/project-one.qmd` | Template for a full write-up (duplicate for each project) |
| `_quarto.yml` | Site title, navbar links, GitHub/LinkedIn URLs |
| `custom.scss` | Colors, fonts, spacing |

### Adding a new project post
1. Duplicate `posts/project-one.qmd`
2. Rename it (e.g. `posts/my-regression-project.qmd`)
3. Update the YAML header (title, date, categories)
4. Write your analysis — the blog listing page auto-discovers it

### Adding your photo
Put a headshot at `assets/img/headshot.jpg`, then uncomment the image line in `about.qmd`.

---

## 🛠 Local Preview Commands (RStudio Terminal)

```bash
quarto preview          # Live preview in browser
quarto render           # Full build to /docs
quarto render index.qmd # Render single file
```

---

## File Structure

```
owen-heap-portfolio/
├── _quarto.yml          # Site config
├── custom.scss          # Styles
├── index.qmd            # Home page
├── about.qmd            # About page
├── projects.qmd         # Projects page
├── posts/
│   ├── index.qmd        # Blog listing (auto-generated)
│   └── project-one.qmd  # Example post (duplicate for each project)
├── assets/img/          # Put images here
├── .github/workflows/
│   └── deploy.yml       # Auto-deploy on push
└── owen-heap-portfolio.Rproj
```
