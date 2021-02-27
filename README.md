## PR Panel

A homebrew project to retrieve pull request information from one or more GitHub repos, and reformat into a simple dashboard-style overview in HTML.

This is written with a Raspberry Pi Zero W plus small colour screen in mind, with the intention for it to sit underneath the main monitor and give an at-a-glance overview of the CI status checks for all active pull requests in a set of target repositories.

### Additional Setup Instructions

#### Required Python Modules

```
pip3 install airium flask pygithub toml
```

#### Disable Power Management / Screensaver and Start Chromium

Place the following in `/home/pi/.config/lxsession/LXDE-pi/autostart`

````
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk http://localhost:5000
````

This will disable power management of the screen, prevent the screensaver from starting, and run the Chromium browser in kiosk mode, pointing it to the Flask server started by the `pr-panel` service.

#### Add Service to SystemD

_Note that the following service script assumes that `pr-panel` is installed in `/opt/pr-panel`. If you have put is somewhere else, the `pr-panel.service` script needs to be modified accordingly._

Copy the script in the `pr-panel/services` directory to `/lib/systemd/system/`:

```
sudo cp services/pr-panel.service /lib/systemd/system/
```

#### Enable the Service

The `pr-panel.service` launches the python script to retrieve and serve the PR data (`pr-panel.service`). The script run by the service also auto-updates from the GitHub repo when it starts, to ensure that the code is the latest version available.

```
sudo systemctl enable pr-panel
```

#### Reboot

A reboot should set everything up.
