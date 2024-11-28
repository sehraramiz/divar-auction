### Project Setup
- install [uv](https://docs.astral.sh/uv/getting-started/installation)
- clone this project
- cd into project root directory
- create .env file from .template.env, set variables
- run ```$ PORT=8080 sh scripts/run.sh```

### Auction Flows

### Auction details page
- when auction exists (started) and the user entering details page is the seller (auction owner):

```mermaid
sequenceDiagram
    actor U as User (Seller)
    participant Divar
    participant WidgetView
    participant Auc as Auction
    participant AucDB as AuctionDB
    U->>+Auc: divar redirects user to Auction /home page
    Auc->>+AucDB: has the auction started, and who is its seller?
    AucDB->>-Auc: auction has started, current user is the auction seller
    Auc->>-U: redirect seller to divar oauth
    U->>+Divar: Authorize app with permissions
    Divar->>-U: redirect user to Auction redirect url with code
    U->>+Auc: See auction details
    Auc->>+AucDB: verify, read auction
    Auc->>+Divar: verify, read ad
    Auc->>+Divar: verify, read user using user auth code
    Auc->>-U: show auction detail page with list of all bidders and auction controls
```

---

- when auction not exists (not started yet) and the user entering details page want to start an auction:

```mermaid
sequenceDiagram
    actor U as User (Creating Ad)
    participant Divar
    participant WidgetView
    participant Auc as Auction
    participant AucDB as AuctionDB
    U->>+Auc: divar redirects user to Auction /home page
    Auc->>+AucDB: has the auction started, and who is its seller?
    AucDB->>-Auc: there is no auction with this ad
    Auc->>+Divar: verify, read ad
    Divar->>-Auc: ad is valid
    Auc->>-U: redirect seller to divar oauth
    U->>+Divar: Authorize app with permissions
    Divar->>-U: redirect user to Auction redirect url with code
    U->>+Auc: See auction details page
    Auc->>+Divar: verify, read ad
    Auc->>+Divar: verify, read user using user auth code
    Auc->>+AucDB: start auction, save auction
    Auc->>-U: show auction detail page with list of all bidders and auction controls
    Auc-->U: redirect user back to divar
```

---

- when auction exists (started) and the user entering details page is not the seller and wants to place a bid:

```mermaid
sequenceDiagram
    actor U as User (Bidder)
    participant Divar
    participant WidgetView
    participant Auc as Auction
    participant AucDB as AuctionDB
    U->>+Auc: divar redirects user to Auction /home page
    Auc->>+AucDB: has the auction started, and who is its seller?
    AucDB->>-Auc: auction has started and this user is not the seller
    Auc->>+Divar: verify, read ad
    Divar->>-Auc: ad is valid
    Auc->>-U: redirect bidder to divar oauth
    U->>+Divar: Authorize app with permissions
    Divar->>-U: redirect bidder to Auction redirect url with code
    U->>+Auc: i want to see auction details page
    Auc->>+Divar: verify, read ad
    Auc->>+Divar: verify, read user using user auth code
    Auc->>-U: show auction detail page with bids count and option to place new bid
    U->>+Auc: i want to place a new bid
    Auc->>AucDB: store new bid on auction
    Auc->>-U: redirect user back to divar
```

#### Placing a bid

```mermaid
sequenceDiagram
    actor Bidder
    participant Divar
    participant WidgetView
    participant Auction
    Bidder->>+Divar: open Ad page
    Bidder->>+WidgetView: sees widget info on divar
    Bidder->>+WidgetView: click on Auction button
    Bidder->>+Auction: redirects to Auction /home page
    Auction->>+Divar: redirect user to Auth page
    Divar->>Auction: authorize app, redirect user to redirect url with auth code, state
    Auction->>+Divar: verify user, get phone number
    Auction->>+AuctionDB: verify ad
    Auction->>+Divar: verify ad token
    Bidder->>+Auction: place bid on auction
    Auction->>+AuctionDB: store new bid
    Auction->>+Bidder: bid placed, redirect to divar
    Bidder->>+Divar: redirects back to divar
```
