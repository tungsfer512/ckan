USER_ADMIN=$(ckan --config /etc/ckan/production.ini user list | grep admin)
if [ $USER_ADMIN != 'name=admin' ]; then
  echo y | ckan --config /etc/ckan/production.ini user add admin email=admin@gmail.com password=12345678
  ckan --config /etc/ckan/production.ini sysadmin add admin
fi