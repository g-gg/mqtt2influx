sudo cp mqtt2influx.service /etc/systemd/system/
sudo systemctl enable mqtt2influx.service
sudo systemctl start mqtt2influx.service
