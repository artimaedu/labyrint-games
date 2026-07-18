# Arrow Path to Treasure — build & install
#
# PyInstaller cannot cross-compile: run each build target on its own OS.
#   build-linux   -> run on Linux
#   build-windows -> run on Windows (Git Bash / MSYS2 make; venv uses Scripts/)
#   build-mac     -> run on an Apple Silicon Mac (needs arm64/universal2 Python)
#
# `make install` builds and installs the game for the current Linux user
# (~/.local/bin plus a desktop entry and icon). Override with PREFIX=/usr make install.

APP    := arrow-path-to-treasure
PY     := .venv/bin/python
PY_WIN := .venv/Scripts/python.exe
PREFIX ?= $(HOME)/.local

.PHONY: venv run build-linux build-windows build-mac install uninstall clean

venv:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements.txt

run:
	$(PY) main.py

build-linux:
	$(PY) -m pip install --quiet pyinstaller
	$(PY) -m PyInstaller --noconfirm --clean --onefile --windowed --name $(APP) \
		--add-data "assets:assets" main.py

build-windows:
	$(PY_WIN) -m pip install --quiet pyinstaller
	$(PY_WIN) -m PyInstaller --noconfirm --clean --onefile --windowed --name $(APP) \
		--add-data "assets;assets" main.py

build-mac:
	$(PY) -m pip install --quiet pyinstaller
	$(PY) -m PyInstaller --noconfirm --clean --onefile --windowed --name $(APP) \
		--target-arch arm64 --add-data "assets:assets" main.py

install: build-linux
	install -Dm755 dist/$(APP) $(PREFIX)/bin/$(APP)
	$(PY) tools/make_icon.py dist/$(APP).png
	install -Dm644 dist/$(APP).png $(PREFIX)/share/icons/hicolor/256x256/apps/$(APP).png
	install -Dm644 packaging/$(APP).desktop $(PREFIX)/share/applications/$(APP).desktop
	-update-desktop-database $(PREFIX)/share/applications 2>/dev/null || true

uninstall:
	rm -f $(PREFIX)/bin/$(APP)
	rm -f $(PREFIX)/share/icons/hicolor/256x256/apps/$(APP).png
	rm -f $(PREFIX)/share/applications/$(APP).desktop

clean:
	rm -rf build dist $(APP).spec
