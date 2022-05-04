# Like Server

## Prep work

PowerShell

```
$Env:DB_USER = "user"
$Env:DB_PASSWORD = "pass"
$Env:DB_NAME = "db"
```


## Run server

v2

```
uvicorn like-server-v2:app --reload
```

v1

```
python3 like-server.py
```

It will access MongoDB to get scores and to save new votes.

Here are the examples how to use it from React application

## Get scores

```
const requestOptions = {
  headers: { 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
};
fetch('http://localhost:10000/likes?' + new URLSearchParams({
  url: this.pageUrl
}), requestOptions)
  .then(response => response.json())
  .then(data => {
    if (data.scores === null) return
    Object.entries(data.scores).forEach(([name, score]) => {
      this.scores[name] = score
    })
    this.forceUpdate()
  });
```

## Increment one score

```
const requestOptions = {
  method: 'POST',
  headers: { 
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    url: this.pageUrl,
    like: scoreName
  })
};
fetch('http://localhost:10000/like', requestOptions)
  .then(response => response.json())
  .then(data => {
    this.scores[data.scoreName] = data.score
    this.forceUpdate()
  });
```