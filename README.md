## Form Automation Worker

### Requirements

- Python 3.10+
- Playwright
- CapSolver

### Installation

```bash
pip install -r requirements.txt
```

### Usage

```bash
python main.py
```

### CapSolver Extension

- Download the CapSolver extension from the [Chrome Web Store](https://chromewebstore.google.com/detail/capsolver-captcha-solver/jgjgjgjgjgjgjgjgjgjgjgjgjgjgjgjg)
- Extract the extension to the `extension` directory
- Run the main.py file

### CapSolver API

- Get your API key from the [CapSolver Dashboard](https://capsolver.com/dashboard)
- Set your API key in the `.env` file
- Run the main.py file

### CapSolver Website Key

- Get your website key from the [CapSolver Dashboard](https://capsolver.com/dashboard)
- Set your website key in the `extension/assets/config.js` file
- Run the main.py file

# Worker sessions

## Running the worker with python

1. update the .env file with the correct values
2. run the main.py file
3. you can run multiple instances of the worker by running the main.py file multiple times or using docker compose

## Running the worker with docker compose (recommended)

1. update the .env file with the correct values
2. update the compose.yml file with the correct values
3. run the docker compose up command

```bash
docker compose up --d
```

### Docker Compose Down

```bash
docker compose down
```

### Docker Compose Build

```bash
docker-compose up --build --remove-orphans
```

### Docker Compose Logs

```bash
docker compose logs -f
```

### Docker Compose Scale

1. edit the compose.yml file to change the number of replicas (default is 5)
2. run the docker compose up command

```bash
docker compose up --d
```

Built with ❤️ by [@evy04](https://github.com/evy04)
Built with ❤️ by [@mizety](https://github.com/mizety)
