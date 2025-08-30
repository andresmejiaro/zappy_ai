## This is 42 machine specific
VENV ?= $(HOME)/py312
PY ?= $(VENV)/bin/python
PIP ?= $(VENV)/bin/pip
HOST ?= 127.0.0.1
PORT ?= 4444
N    ?= 13
NAME ?= pollo


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


.PHONY: all clean fclean re 