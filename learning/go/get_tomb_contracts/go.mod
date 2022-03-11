module tomb.contracts

go 1.17

replace tomb.contracts/rest => ./rest

replace tomb.contracts/getter => ./contract_getter

require tomb.contracts/getter v0.0.0-00010101000000-000000000000

require tomb.contracts/rest v0.0.0-00010101000000-000000000000 // indirect
