## This is 42 machine specific
VENV ?= $(HOME)/py312
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
HOST ?= 127.0.0.1
PORT ?= 4444
N    ?= 13
NAME ?= pollo

LOCAL_VENV ?= $(CURDIR)/.venv
LOCAL_PY ?= $(LOCAL_VENV)/bin/python
LOCAL_PIP ?= $(LOCAL_VENV)/bin/pip

DEMO_HOST ?= 127.0.0.1
DEMO_PORT ?= 4242
DEMO_TEAM ?= pollo
DEMO_WIDTH ?= 10
DEMO_HEIGHT ?= 10
DEMO_SLOTS ?= 4
DEMO_AGENTS ?= 16
DEMO_TICK ?= 100
DEMO_LOG_DIR ?= $(CURDIR)/.local/demo
GODOT_ARGS ?=
DEMO_VIDEO_SECONDS ?= 20
DEMO_VIDEO_WARMUP ?= 8
DEMO_VIDEO_FPS ?= 30
DEMO_VIDEO_OUT ?=
DEMO_MODE ?=
DEMO_RECORD_PROTOCOL ?=
DEMO_REPLAY_FILE ?=
DEMO_MONTAGE_OUT ?=
DEMO_MONTAGE_RECORD_SECONDS ?= 150
DEMO_MONTAGE_AUDIO_FILES ?=


all: client


client:
	$(PIP) install numpy
	$(PIP)  install -e .
	$(PY) -m zipapp src -m 'zappy_ai.client:main' \
  		-p $(PY) \
  		-o client
	chmod +x client	

clean:
	$(PIP)  uninstall -y numpy zappy_ai
	rm -f client

fclean: clean

re: fclean all

run-clients:
	@seq $(N) | xargs -n1 -P $(N) -I{} \
	  "$(PY)" -m zappy_ai.client -h "$(HOST)" -p "$(PORT)" -n "$(NAME)"

demo-preflight:
	@echo "Server binary: $(CURDIR)/external/zappy/server"
	@test -x "$(CURDIR)/external/zappy/server"
	@echo "Python: $(LOCAL_PY)"
	@"$(LOCAL_PY)" --version
	@GODOT_BIN="$$(./scripts/find_godot.sh)"; \
	  echo "Godot: $$GODOT_BIN"; \
	  "$$GODOT_BIN" --version

demo-ai-install:
	@"$(LOCAL_PIP)" install -e . --no-build-isolation

demo-server:
	@echo "Starting server on $(DEMO_HOST):$(DEMO_PORT) for team $(DEMO_TEAM)"
	@./external/zappy/server -p "$(DEMO_PORT)" -x "$(DEMO_WIDTH)" -y "$(DEMO_HEIGHT)" -n "$(DEMO_TEAM)" -c "$(DEMO_SLOTS)" -t "$(DEMO_TICK)"

demo-gui:
	@DEMO_MODE="$(DEMO_MODE)" \
	  DEMO_RECORD_PROTOCOL="$(DEMO_RECORD_PROTOCOL)" \
	  DEMO_REPLAY_FILE="$(DEMO_REPLAY_FILE)" \
	  DEMO_WIDTH="$(DEMO_WIDTH)" \
	  DEMO_HEIGHT="$(DEMO_HEIGHT)" \
	  ./scripts/run_gui.sh $(GODOT_ARGS)

demo-ai:
	@echo "Starting AI client against $(DEMO_HOST):$(DEMO_PORT) as team $(DEMO_TEAM)"
	@"$(LOCAL_PY)" -m zappy_ai.client -h "$(DEMO_HOST)" -p "$(DEMO_PORT)" -n "$(DEMO_TEAM)"

demo-full:
	@DEMO_HOST="$(DEMO_HOST)" \
	  DEMO_PORT="$(DEMO_PORT)" \
	  DEMO_TEAM="$(DEMO_TEAM)" \
	  DEMO_WIDTH="$(DEMO_WIDTH)" \
	  DEMO_HEIGHT="$(DEMO_HEIGHT)" \
	  DEMO_AGENTS="$(DEMO_AGENTS)" \
	  DEMO_SLOTS="$(DEMO_SLOTS)" \
	  DEMO_TICK="$(DEMO_TICK)" \
	  DEMO_LOG_DIR="$(DEMO_LOG_DIR)" \
	  DEMO_MODE="$(DEMO_MODE)" \
	  DEMO_RECORD_PROTOCOL="$(DEMO_RECORD_PROTOCOL)" \
	  DEMO_REPLAY_FILE="$(DEMO_REPLAY_FILE)" \
	  GODOT_ARGS="$(GODOT_ARGS)" \
	  ./scripts/demo_full.sh

demo-video:
	@DEMO_HOST="$(DEMO_HOST)" \
	  DEMO_PORT="$(DEMO_PORT)" \
	  DEMO_TEAM="$(DEMO_TEAM)" \
	  DEMO_WIDTH="$(DEMO_WIDTH)" \
	  DEMO_HEIGHT="$(DEMO_HEIGHT)" \
	  DEMO_AGENTS="$(DEMO_AGENTS)" \
	  DEMO_SLOTS="$(DEMO_SLOTS)" \
	  DEMO_TICK="$(DEMO_TICK)" \
	  DEMO_LOG_DIR="$(DEMO_LOG_DIR)" \
	  DEMO_MODE="1" \
	  DEMO_RECORD_PROTOCOL="$(DEMO_RECORD_PROTOCOL)" \
	  DEMO_REPLAY_FILE="" \
	  DEMO_VIDEO_SECONDS="$(DEMO_VIDEO_SECONDS)" \
	  DEMO_VIDEO_WARMUP="$(DEMO_VIDEO_WARMUP)" \
	  DEMO_VIDEO_FPS="$(DEMO_VIDEO_FPS)" \
	  DEMO_VIDEO_OUT="$(DEMO_VIDEO_OUT)" \
	  GODOT_ARGS="$(GODOT_ARGS)" \
	  ./scripts/demo_video.sh

demo-replay-video:
	@DEMO_HOST="$(DEMO_HOST)" \
	  DEMO_PORT="$(DEMO_PORT)" \
	  DEMO_TEAM="$(DEMO_TEAM)" \
	  DEMO_WIDTH="$(DEMO_WIDTH)" \
	  DEMO_HEIGHT="$(DEMO_HEIGHT)" \
	  DEMO_AGENTS="$(DEMO_AGENTS)" \
	  DEMO_SLOTS="$(DEMO_SLOTS)" \
	  DEMO_TICK="$(DEMO_TICK)" \
	  DEMO_LOG_DIR="$(DEMO_LOG_DIR)" \
	  DEMO_MODE="1" \
	  DEMO_RECORD_PROTOCOL="" \
	  DEMO_REPLAY_FILE="$(DEMO_REPLAY_FILE)" \
	  DEMO_VIDEO_SECONDS="$(DEMO_VIDEO_SECONDS)" \
	  DEMO_VIDEO_WARMUP="$(DEMO_VIDEO_WARMUP)" \
	  DEMO_VIDEO_FPS="$(DEMO_VIDEO_FPS)" \
	  DEMO_VIDEO_OUT="$(DEMO_VIDEO_OUT)" \
	  GODOT_ARGS="$(GODOT_ARGS)" \
	  ./scripts/demo_video.sh

demo-ai-video:
	@DEMO_HOST="$(DEMO_HOST)" \
	  DEMO_PORT="$(DEMO_PORT)" \
	  DEMO_TEAM="$(DEMO_TEAM)" \
	  DEMO_WIDTH="$(DEMO_WIDTH)" \
	  DEMO_HEIGHT="$(DEMO_HEIGHT)" \
	  DEMO_AGENTS="$(DEMO_AGENTS)" \
	  DEMO_SLOTS="$(DEMO_SLOTS)" \
	  DEMO_TICK="$(DEMO_TICK)" \
	  DEMO_LOG_DIR="$(DEMO_LOG_DIR)" \
	  DEMO_REPLAY_FILE="$(DEMO_REPLAY_FILE)" \
	  DEMO_MONTAGE_OUT="$(DEMO_MONTAGE_OUT)" \
	  DEMO_MONTAGE_RECORD_SECONDS="$(DEMO_MONTAGE_RECORD_SECONDS)" \
	  DEMO_MONTAGE_AUDIO_FILES="$(DEMO_MONTAGE_AUDIO_FILES)" \
	  "$(LOCAL_PY)" ./scripts/render_zappy_ai_video.py

.PHONY: all clean fclean re run-clients demo-preflight demo-ai-install demo-server demo-gui demo-ai demo-full demo-video demo-replay-video demo-ai-video
