class StaticCurrency:

    blockchains = {
        "tron": {
            "tokens": [
                {
                    'name': 'USDT',
                    'contract_address': "TR7NHqjeKQxGTCi8q8ZY4pL8otSzgjLj6t",
                    "network": {
                        'name': 'mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "TRC-20",
                    "algorithm": 'TRC-20'
                },
                {
                    'name': 'USDT',
                    'contract_address': "TXLAQ63Xg1NAzckPwKHvzw7CSEmLMEqcdj",
                    "network": {
                        'name': 'nile',
                        'mainnet': False
                    },
                    "display_algorithm": "TRC-20 TESTNET",
                    "algorithm": 'TRC-20'
                },
                {
                    'name': "TRX",
                    'contract_address': None,
                    "network": {
                        'name': 'nile',
                        'mainnet': False
                    },
                    "display_algorithm": "TRC-20 TESTNET",
                    "algorithm": 'TRC-20'
                },
                {
                    'name': "TRX",
                    'contract_address': None,
                    "network": {
                        'name': 'mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "TRC-20",
                    "algorithm": 'TRC-20'
                }
            ]
        },
        "ethereum": {
            "tokens": [
                {
                    'name': "ETH",
                    'contract_address': None,
                    "network": {
                        'name': 'mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "ERC-20",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "ETH",
                    'contract_address': None,
                    "network": {
                        'name': 'goerli',
                        'mainnet': False
                    },
                    "display_algorithm": "ERC-20 TESTNET",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "MATIC",
                    'contract_address': None,
                    "network": {
                        'name': 'polygon-mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "Polygon",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "MATIC",
                    'contract_address': None,
                    "network": {
                        'name': 'polygon-mumbai',
                        'mainnet': False
                    },
                    "display_algorithm": "Polygon TESTNET",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "Arbitrum",
                    'contract_address': None,
                    "network": {
                        'name': 'arbitrum-mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "Arbitrum",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "Arbitrum",
                    'contract_address': None,
                    "network": {
                        'name': 'arbitrum-goerli',
                        'mainnet': False
                    },
                    "display_algorithm": "Arbitrum TESTNET",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "Optimism",
                    'contract_address': None,
                    "network": {
                        'name': 'optimism-mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "Optimism",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "Optimism",
                    'contract_address': None,
                    "network": {
                        'name': 'optimism-goerli',
                        'mainnet': False
                    },
                    "display_algorithm": "Optimism TESTNET",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "USDT",
                    'contract_address': "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                    "network": {
                        'name': 'mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "ERC-20",
                    "algorithm": 'ERC-20'
                },
                {
                    'name': "USD",
                    'contract_address': "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                    "network": {
                        'name': 'mainnet',
                        'mainnet': True
                    },
                    "display_algorithm": "ERC-20",
                    "algorithm": 'ERC-20'
                }
            ]
        }
    }
