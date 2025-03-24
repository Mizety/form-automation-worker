
# Navigate to the working directory
# cd ~/form-automation-worker || exit

# Activate the virtual environment
source venv/bin/activate

## Generate config
python config_extension.py

# we want to run with pm2 for production
## Worker 1
pm2 start "xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python main.py" --name "form-automation-worker 1"  --exp-backoff-restart-delay=100

## Worker 2
pm2 start "xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python main.py" --name "form-automation-worker 2"  --exp-backoff-restart-delay=100

## Worker 3
pm2 start "xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python main.py" --name "form-automation-worker 3"  --exp-backoff-restart-delay=100

## Worker 4
pm2 start "xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python main.py" --name "form-automation-worker 4"  --exp-backoff-restart-delay=100

## Worker 5
pm2 start "xvfb-run --auto-servernum --server-args='-screen 0 1920x1080x24' python main.py" --name "form-automation-worker 5"  --exp-backoff-restart-delay=100
