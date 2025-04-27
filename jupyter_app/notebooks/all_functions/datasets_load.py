import pandas as pd

def load_all_datasets():
    '''Функция возвращает 10 исследуемых датасетов'''
    crypt_Ethereum = pd.read_csv('../data/cryptocurrency/Ethereum_2016_2024.csv')
    crypt_BTC = pd.read_csv('../data/cryptocurrency/BTC_USD Bitfinex_2016_2024.csv')

    futures_Brent_LCOK5 = pd.read_csv('../data/futures_market_oil/Brent - Май 25 (LCOK5) 2016_2024.csv')
    futures_WTI_CLJ5 = pd.read_csv('../data/futures_market_oil/WTI - Апр 25 (CLJ5) 2016_2024.csv')

    share_metal_jiangxi_copper = pd.read_csv('../data/share_matal_company/jiangxi_copper_hk_2016_2024.csv')
    share_metal_baoshan_iron = pd.read_csv('../data/share_matal_company/baoshan_iron_sh_2016_2024.csv')

    share_oil_petrochina_hk = pd.read_csv('../data/share_oil_gaz_company/petrochina_hk_2016_2024.csv')
    share_oil_equinor_oslo = pd.read_csv('../data/share_oil_gaz_company/equinor_oslo_2016_2024.csv')

    spot_preciouse_metal_AU = pd.read_csv('../data/spot_market_precious_metal/XAU_USD_2016_2024.csv')
    spot_preciouse_metal_AG = pd.read_csv('../data/spot_market_precious_metal/XAG_USD_2016_2024.csv')

    return  crypt_Ethereum, crypt_BTC, futures_Brent_LCOK5, \
            futures_WTI_CLJ5, share_metal_jiangxi_copper, \
            share_metal_baoshan_iron, share_oil_petrochina_hk, \
            share_oil_equinor_oslo, spot_preciouse_metal_AG, spot_preciouse_metal_AU