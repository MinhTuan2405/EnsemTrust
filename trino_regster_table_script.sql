use delta.default

CREATE SCHEMA IF NOT EXISTS delta.warehouse
WITH (location = 's3a://gold/delta/');

CALL delta.system.register_table(
    schema_name => 'warehouse',
    table_name => 'customer',
    table_location => 's3a://gold/delta/customer'
);

CALL delta.system.register_table(
    schema_name => 'warehouse',
    table_name => 'corporate',
    table_location => 's3a://gold/delta/corporate'
);


CALL delta.system.register_table(
    schema_name => 'warehouse',
    table_name => 'home_office',
    table_location => 's3a://gold/delta/home_office'
);



select * from delta.warehouse.corporate;
select * from delta.warehouse.customer;
select * from delta.warehouse.home_office;