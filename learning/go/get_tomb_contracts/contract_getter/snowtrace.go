package snowtrace

import (
  "tomb.contracts/rest"
)

func PrintSnowtraceParams() {
    // TODO: define this somewhere else
    api_key := ""
    token_address := ""
    snowtrace_url := "https://api.snowtrace.io/api"
    p_rest_params := rest.CreateParams(api_key, snowtrace_url)
    rest.PrintRestParams(p_rest_params)
    rest.GetTransactions(token_address, p_rest_params)
}
