package rest

import (
//    "fmt"
    "net/http"
    io "io/ioutil"
    "log"
//     "os"
)

type QueryParams map[string]string
// type FnGetTransactions func(string, *RestParams) (map[string]interface{})
// type AddQueryParameters func(*Request, map[string]int) string

var g_http_client *http.Client = nil

func GetHttpClient() *http.Client {
    if g_http_client == nil {
        g_http_client = &http.Client{}
    }
    return g_http_client
}

func GetTransactions(
    base_uri string,
    p_query_params *QueryParams,
) []byte {
    req, err := http.NewRequest("GET", base_uri, nil)

    if err != nil {
        log.Fatal(err)
    }

    q := req.URL.Query()

    for k, v := range (*p_query_params) {
        q.Add(k, v)
    }

    req.URL.RawQuery = q.Encode()

    p_resp, err := GetHttpClient().Do(req)

    if err != nil {
        log.Fatal(err)
    }

    defer p_resp.Body.Close()
    body, err := io.ReadAll((*p_resp).Body)

    if err != nil {
        log.Fatal(err)
    }

    return body
}
