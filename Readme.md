# Start a command from prometheus alerts delivered via webhook

This is a simple server that will listen for alerts via webhook and runs
commands.

## Configuration

It needs a yaml-config file (defaults to /etc/prometheus/alerthooks.yml) of
the following format.

```yaml
/route/
  command: my_mailer -s "alert happended" user@example.com
```

The script will get the alert as stdin.
