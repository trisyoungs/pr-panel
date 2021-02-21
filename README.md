## PR Panel

A homebrew project to retrieve pull request information from one or more GitHub repos, and reformat into a simple dashboard-style overview in HTML.

This is written with a Raspberry Pi Zero W plus small colour screen in mind, with the intention for it to sit underneath the main monitor and give an at-a-glance overview of the CI status checks for all active pull requests in a set of target repositories.

### Additional Setup Instructions

#### Required Python Modules

```
pip3 install markuppy flask pygithub
```

#### Enable Chromium Autostart in Kiosk Mode

Place the following in `/home/pi/.config/lxsession/LXDE-pi/autostart`
````
@xset s off
@xset -dpms
@xset s noblank
@chromium-browser --kiosk http://localhost:5000
````

#### Run Script On Startup

Easy via cron:

```
sudo crontab -e
```

Add the line (adjusting the path to suit):

```
@reboot python3 /home/pi/pr-panel/myscript.py
```
