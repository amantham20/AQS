.PHONY: build install clean test

BINARY_NAME=aqs
INSTALL_PATH=/usr/local/bin

build:
	go build -ldflags="-s -w" -o $(BINARY_NAME) .

install: build
	cp $(BINARY_NAME) $(INSTALL_PATH)/$(BINARY_NAME)

uninstall:
	rm -f $(INSTALL_PATH)/$(BINARY_NAME)

clean:
	rm -f $(BINARY_NAME)

test:
	go test -v ./...

# Cross-compile for different platforms
build-all:
	GOOS=darwin GOARCH=amd64 go build -ldflags="-s -w" -o $(BINARY_NAME)-darwin-amd64 .
	GOOS=darwin GOARCH=arm64 go build -ldflags="-s -w" -o $(BINARY_NAME)-darwin-arm64 .
	GOOS=linux GOARCH=amd64 go build -ldflags="-s -w" -o $(BINARY_NAME)-linux-amd64 .
	GOOS=linux GOARCH=arm64 go build -ldflags="-s -w" -o $(BINARY_NAME)-linux-arm64 .
