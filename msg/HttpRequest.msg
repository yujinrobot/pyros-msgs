# This comes from requests package API

# possible HTTP methods
uint8 HEAD = 0
uint8 OPTIONS = 1
uint8 GET = 2
uint8 POST = 3
uint8 PUT = 4
uint8 PATCH = 5
uint8 DELETE = 6

uint8 method
string url

string params
string headers
string data

bool allow_redirects
float32 timeout