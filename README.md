# BX - Catppuccin Mocha Todo App

A beautiful todo application styled with the Catppuccin Mocha color palette, built with PuePy and Tailwind CSS.

## Features

- ✨ Beautiful Catppuccin Mocha theme
- 📝 Add, complete, and remove todos
- 💾 Persistent state using OPFS (Origin Private File System)
- 🎨 Modern UI with smooth transitions
- 📱 Responsive design

## Local Development

### Prerequisites

- Node.js 18+
- Python 3.11+

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Build CSS:
   ```bash
   npm run build
   ```

3. Serve the application:
   ```bash
   python -m http.server 8000
   ```

4. Open http://localhost:8000

## Docker

### Build and Run with Docker

```bash
# Build the image
docker build -t bx-app .

# Run the container
docker run -p 8000:8000 bx-app
```

### Using Docker Compose

```bash
# Build and run with docker-compose
docker-compose up --build

# Run in background
docker-compose up -d
```

## GitHub Container Registry

The application is automatically built and pushed to GitHub Container Registry (GHCR) on every push to main/master branch.

### Pull and Run from GHCR

```bash
# Pull the latest image
docker pull ghcr.io/codegod100/bx:latest

# Run the container
docker run -p 8000:8000 ghcr.io/codegod100/bx:latest
```

## Technology Stack

- **Frontend**: PuePy (Python web framework)
- **Styling**: Tailwind CSS v4
- **Theme**: Catppuccin Mocha
- **Font**: Inter (Google Fonts)
- **Container**: Docker
- **Registry**: GitHub Container Registry (GHCR)

## Color Palette

This application uses the official Catppuccin Mocha color palette:

- **Base**: Dark background (`#1e1e2e`)
- **Surface**: Card backgrounds (`#313244`, `#45475a`)
- **Text**: Light text (`#cdd6f4`)
- **Accents**: Blue, Green, Red, Mauve for various UI elements

## License

ISC
