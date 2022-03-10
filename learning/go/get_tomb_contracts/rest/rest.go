package rest

import (
    "fmt"
    "net/http"
    io "io/ioutil"
    "log"
//     "os"
)

type RestParams struct {
    api_key string
    base_uri string
    http_client *http.Client
}

func CreateParams(api_key string, base_uri string) *RestParams {
    p_rest_params := new(RestParams)
    p_rest_params.api_key = api_key
    p_rest_params.base_uri = base_uri
    p_rest_params.http_client = &http.Client{}
    return p_rest_params
}

func PrintRestParams(p_rest_params *RestParams) {
    fmt.Println((*p_rest_params).api_key)
    fmt.Println((*p_rest_params).base_uri)
}

func GetTransactions(token_addr string, p_rest_params *RestParams) {
    req, err := http.NewRequest("GET", (*p_rest_params).base_uri, nil)
    if err != nil {
        log.Fatal(err)
    }

    // add additional queries required based on 
    // TODO: this example is specific to snowtrace, move to snowtrace and have
    // a argument to grab this
    q := req.URL.Query()
    q.Add("apikey", (*p_rest_params).api_key)
    q.Add("module", "account")
    q.Add("action", "txlist")
    q.Add("address", token_addr)
    q.Add("startblock", "1")
    q.Add("endblock", "999999999")
    q.Add("sort", "asc")
    q.Add("offset", "10")
    q.Add("page", "1")
    req.URL.RawQuery = q.Encode()

    // parse response
    p_resp, err := p_rest_params.http_client.Do(req)
    if err != nil {
        log.Fatal(err)
    }

    defer p_resp.Body.Close()

    body, err := io.ReadAll((*p_resp).Body)
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("%s", body)
}
