AGRI GENIE - QUICK RUN (NO BUILD)

This package is prepared for demo use on another Windows computer.

1) Install Docker Desktop
   - Download and install Docker Desktop for Windows.
   - Open Docker Desktop and wait until it says Docker is running.

2) Run the app
   - Double-click run_app.bat
   - It will:
     a) load the prebuilt image archive (agrigenie.tar)
     b) start the app with docker compose
     c) show the URL

3) Open in browser
   - Default: http://localhost:8000
   - If port 8000 is already used, launcher auto-switches to:
     http://localhost:8001

4) Stop the app later
  - Double-click stop_app.bat
  - (Optional terminal method: docker compose down)

Notes for reliable demo:
- Keep these files in the same folder:
  - run_app.bat
  - stop_app.bat
  - agrigenie.tar
  - docker-compose.yml
  - .env
- Do not rename agrigenie.tar unless you also update run_app.bat.
- First startup can take a little time while containers initialize.

If startup fails:
- Make sure Docker Desktop is running.
- Re-run run_app.bat as normal user first.
- If needed, right-click run_app.bat and choose "Run as administrator".


Remove-Item *.aux, *.log, *.out, *.toc, *.lof, *.lot -ErrorAction SilentlyContinue
pdflatex KUET_Report_AgriGenie.tex