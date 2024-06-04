# News Sender Bot

A Slack bot for sending news articles from various sources to a specified channel. This bot fetches news articles using APIs and sends them to users on a scheduled basis or on demand.

## Features

- Fetches news articles from multiple sources
- Sends news to Slack channel
- Schedules news updates
- Supports various news APIs
- Easy configuration and setup

## Getting Started

### Prerequisites

- Python 3.7 or higher
- A Slack bot token (you can create one by visiting the [Slack API](https://api.slack.com/))
- API keys for the news sources you wish to use (e.g., NewsAPI)

### Installation

1. Clone the repository:

   ```sh
   git clone https://github.com/seilk/news-sender-bot.git
   cd news-sender-bot
   ```
2. Install the required packages:

   ```sh
   conda env create -f requirements.yaml
   ```
3. Configure the bot:

   - Make CONSTANT.py and configure the file:

     ```sh
     # touch CONSTANT.py
     slack_token="your-slack-token"
     slack_channel_id="your-slack-channel-id"
     ```
   - Edit the `config.yaml` file to add your Slack bot token and news API keys.

### Usage

1. Run the bot:
   ```
   python slack_news_boy.py
   ```


## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE]() file for details.

## Acknowledgements

* [Slack](https://slack.com/)
* All contributors and supporters
