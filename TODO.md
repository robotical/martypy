# Outstanding items

- ensure there is a celebrate trajectory on Marty 2
- implement get_distance_sensor() in Marty 2
- implement colour sensor get/clear? on Marty 2
- implement IR feet handling on Marty 2
- discover returns empty list on Marty 2, maybe something better is a good idea?
- ensure trajectory parameters are correctly bounded (turn parameter, eye/arm max angles, etc)

# Items probably not worth implementing as they can be achieved another way
- enable/disable safeties, fall-detection, motors on Marty 2 (can be done using send_ric_rest_cmd())
- consider I2C direct access commands on Marty 2 (can be done using send_ric_rest_cmd_sync())
- consider API for naming/configuring add-ons (can be done using send_ric_rest_cmd_sync())
- consider implementing separate API for WiFi setup (can be done using send_ric_rest_cmd())

