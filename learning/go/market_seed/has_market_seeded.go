package main

import (
	"encoding/json"
	"io"
	"log"
	"net/http"
)

type TransactionsResponse struct {
	Status  string
	Message string
	Result  []map[string]interface{}
}

var g_http_client *http.Client = nil

func GetHttpClient() *http.Client {
	if g_http_client == nil {
		g_http_client = &http.Client{}
	}
	return g_http_client
}

func main() {
	hasMarketSeeded()
	// go forever()

	// quitChannel := make(chan os.Signal, 1)
	// signal.Notify(quitChannel, syscall.SIGINT, syscall.SIGTERM)
	// <-quitChannel
	// //time for cleanup before exit
	// fmt.Println("Adios!")
}

func hasMarketSeeded() bool {
	const snowtraceAPI = "https://api.snowtrace.io/api"
	const contractAddress = "0x8bea96dbe7c85127a68ad6916949670eb5c45e9c"
	const apiKey = "34KGG6F4JJ1DE5IZI7IQUK8M8RIQRDN5EM"
	queryParams := map[string]string{
		"apikey":     apiKey,
		"module":     "account",
		"action":     "txlist",
		"address":    contractAddress,
		"startblock": "1",
		"endblock":   "999999999",
		"sort":       "dsc",
		"offset":     "2",
		"page":       "1",
	}

	// Get all transactions from snowtrace
	req, err := http.NewRequest("GET", snowtraceAPI, nil)
	q := req.URL.Query()

	for k, v := range queryParams {
		q.Add(k, v)
	}

	req.URL.RawQuery = q.Encode()
	p_resp, err := GetHttpClient().Do(req)

	log.Println(p_resp)

	if err != nil {
		log.Println("Snowtrace call failed:")
		log.Println(err)
		return false
	}

	defer p_resp.Body.Close()
	body, err := io.ReadAll((*p_resp).Body)

	log.Println(p_resp)

	if err != nil {
		log.Println("Error parsing snowtrace resposne:")
		log.Println(err)
		return false
	}

	dat := TransactionsResponse{}
	json.Unmarshal(body, &dat)

	for i, v := range dat.Result {
		log.Println(i)
		log.Println(v)
	}

	// TODO: get function identifier from metamask
	// TODO: get print out message
	// TODO: check GetBalance() as well

	return true

	// Check if any transaction has the
}

func forever() {
	hasMarketSeeded()
	// for {
	// 	fmt.Printf("%v+\n", time.Now())
	// 	time.Sleep(time.Second)
	// }
}
