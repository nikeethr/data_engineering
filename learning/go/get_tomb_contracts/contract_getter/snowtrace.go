package snowtrace

import (
	"encoding/json"

	"tomb.contracts/rest"
)

type TransactionsResponse struct {
	Status  string
	Message string
	Result  []map[string]interface{}
}

func FindTombContracts() {
	// https://pkg.go.dev/github.com/gochain/web3
	// iterate through transactions of particular owner

	// find contract with allocate seigniorage in ABI

	// Verify contract by checking if token is in treasury

	// Get all token addresses from treasury and check if they match format of
	// different tomb tokens
}

func IsTreasury() {
	// business rules for treasury
}

func IsBoardroom() {
	// business rules for boardroom
}

func IsShareToken() {
	// business rules for share token
}

func IsShareTokenRewardPool() {
	// business rules for share token
}

func GetFirstTransaction() {
	// TODO: managing errors
	query_params := rest.QueryParams{
		"apikey":     "",
		"module":     "account",
		"action":     "txlist",
		"address":    "",
		"startblock": "1",
		"endblock":   "999999999",
		"sort":       "dsc",
		"offset":     "1",
		"page":       "1",
	}
	snowtrace_url := "https://api.snowtrace.io/api"
	body := rest.GetTransactions(snowtrace_url, &query_params)
	dat := TransactionsResponse{}
	json.Unmarshal(body, &dat)
	first_addr := dat.Result[0]["from"].(string)

	return first_addr
}
