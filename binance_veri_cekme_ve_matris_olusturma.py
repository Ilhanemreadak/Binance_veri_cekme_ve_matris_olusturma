from binance import Client
import csv
import pandas as pd
import datetime as dt
import pandas_ta as ta

client = Client(None,None)

"""
    > Binanceden seçilen coinin seçilen zaman aralığına ve periyoduna göre fiyat bilgilerini çekip xlsx dosyasına çeviren kod.
    > İçinde iki tane basit strateji bulundurur bu stratejileri geçmiş verilere uygulayarak stratejilerin sonuçlarını gözlemleyebilirsiniz.
"""



periyotlar = {
    '1m': Client.KLINE_INTERVAL_1MINUTE,
    '3m': Client.KLINE_INTERVAL_3MINUTE,
    '5m': Client.KLINE_INTERVAL_5MINUTE,
    '15m': Client.KLINE_INTERVAL_15MINUTE,
    '30m': Client.KLINE_INTERVAL_30MINUTE,
    '1h': Client.KLINE_INTERVAL_1HOUR,
    '2h': Client.KLINE_INTERVAL_2HOUR,
    '4h': Client.KLINE_INTERVAL_4HOUR,
    '6h': Client.KLINE_INTERVAL_6HOUR,
    '8h': Client.KLINE_INTERVAL_8HOUR,
    '12h': Client.KLINE_INTERVAL_12HOUR,
    '1d': Client.KLINE_INTERVAL_1DAY,
    '3d': Client.KLINE_INTERVAL_3DAY,
    '1w': Client.KLINE_INTERVAL_1WEEK,
    '1M': Client.KLINE_INTERVAL_1MONTH,
}

def csvOlustur(sembol,mumlar):
    dosyaAdi = str(sembol + ".csv")
    csvDosya = open(dosyaAdi,"w", newline='')  # Yazma odaklı csv dosyası olusturuyoruz.
    yazici = csv.writer(csvDosya,delimiter=',')  # Yazıcı olusturuyoruz virguller ile ayırıp satır satır assagıya inecek
    for mumVerileri in mumlar: #Verileri Ayrı satırlarda yazabilmesi icin for dongusu kullanıyoruz.
        yazici.writerow(mumVerileri)  # yaz emri veriyoruz
    csvDosya.close() # dosyayı kapatıyoruz.
    return dosyaAdi

def periyotGir():
    print('PERIYOTLAR')
    for i in periyotlar:
        print(i)
    print("#####################")
    secim = input("Lutfen Periyot Secin : ")
    return periyotlar.get(secim)

def zamanGir(cv):
    print("Lutfen zaman degerini ornekteki gibi giriniz : (17 July 2019)")
    if cv == 0:
        choise = input("Baslangic Zamanini Giriniz : ")
    elif cv ==1:
        choise = input("Bitis Zamanini Giriniz : ")
    else:
        choise = 0

    return choise

def sembolGir():
    coinlist = []
    print("Istediginiz coinleri giriniz.\nLutfen parite ciftlerini dogru giriniz. Ornegin : (BTCUSDT)."
          "\nYeteri kadar coin girdiginizde veri girmeden ENTER yapiniz.")
    while True:
        choise = input("Coin Adi Giriniz :  ")
        if choise =='':
            break
        else:
            coinlist.append(choise)
    return coinlist

def zamanHesapla(timestamp):
    #Binanceden cektigimiz zaman verisini ms cinsinden normal tarihe ceviriyoruz
    return dt.datetime.fromtimestamp(timestamp/1000)

def excelYap(okunacakCsv):
    basliklar = ['open_time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'nat', 'tbbav', 'tbqav',
                 'ignore']
    df = pd.read_csv(okunacakCsv, names=basliklar)
    tarihler = pd.Series(map(lambda x: zamanHesapla(x).date(), df['open_time']))
    saatler = pd.Series(map(lambda x: zamanHesapla(x).time(), df['open_time']))
    total = pd.DataFrame(
        {'Tarih': tarihler, 'Saat': saatler, 'Acilis': df['open'], 'Yuksek': df['high'], 'Dusuk': df['low'],
         'Kapanis': df['close'], 'HacimLot': df['vol'], 'AOrt': 0})
    writer = pd.ExcelWriter(okunacakCsv+".xlsx")
    total.to_excel(writer, sheet_name='Sayfa1', index=False)
    workbook = writer.book
    worksheet = writer.sheets['Sayfa1']
    header_format = workbook.add_format({
        'bold': False,
        'text_wrap': False,
        'valign': 'top'})
    for col_num, value in enumerate(total.columns.values):
        worksheet.write(0, col_num , value, header_format)
    writer.save()

def verileriGetir(sembol,periyot,baslangic,bitis):
    # Sembol isimli coinin datalarini verilen zaman araligina gore donduren metod
    mumlar = client.get_historical_klines(sembol,periyot,baslangic,bitis)
    return mumlar

def veriCekmeVeMatrikseUyarlama(semboller, periyot, baslangic, bitis):
    for coin in semboller:  # semboller dizisinde gezen ve gezdigi her elemanı coin degiskenine atıyan dongu
        excelYap(csvOlustur(coin, verileriGetir(coin, periyot, baslangic, bitis)))
        print(coin, " Verileri Getirildi. ")

def DCA():
    islemBasiDolar = 100
    alimSayisi = 0
    toplamCoin = 0
    komisyonOrani = 75/10000
    verilenKomisyon = 0
    #Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore
    basliklar = ['opentime','open','high','low','close','vol','close_time','qav','nat','tbbav','tbqav','ıgnore']
    print("DCA Stratejisini Uygulamak Istediginiz coini parite cifti ve uzantisiyle birlikte ismini giriniz. Orn : (BTCUSDT.csv)")
    okunacakCsv = input("Coini giriniz : ")

    df = pd.read_csv(okunacakCsv,names=basliklar) #Cekdigimiz verilere basliklar atıyoruz

    open = df['open']
    close = df['close']
    acilisZamani = df['opentime']
    high = df['high']
    low = df['low']

    sma50 = ta.sma(close,length=50)
    print("##### DCA Metod Active #####")
    for i in range(len(close)): #kapanis verilerini tek tek gezen dongu
        if pd.isna(sma50[i]) is False : #isna metodu icine koydugun degerler NaN ise True degilse False donduruyor
            if close[i-1] < sma50[i-1] and close[i] > sma50[i]: #Yukarı kesisim metodu fiyat sma50yi yukarı yonde kestimi
                print(zamanHesapla(acilisZamani[i+1]),"tarihinde",islemBasiDolar/close[i],"adet BTC alındı")
                print("##################")
                alimSayisi +=1
                toplamCoin+=islemBasiDolar/close[i]
                verilenKomisyon+= komisyonOrani*islemBasiDolar
    print("Toplam Yapılan islem : ", alimSayisi)
    print("Toplam Alinan Coin : ", toplamCoin)
    print("Toplam Yatirim : ", alimSayisi*islemBasiDolar)
    print("Su anki cuzdan tutari : ", toplamCoin* close[len(close)-1]-verilenKomisyon)
    print("Guncel Kar : %",(toplamCoin* close[len(close)-1]-verilenKomisyon)/(alimSayisi*islemBasiDolar)*100-100)

def gdCross():
    cuzdan = 100
    alimSayisi = 0
    satimSayisi =0
    toplamCoin = 0
    komisyonOrani = 75/10000
    verilenKomisyon = 0
    #Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore
    basliklar = ['opentime','open','high','low','close','vol','close_time','qav','nat','tbbav','tbqav','ıgnore']

    print("Golden-Dead Cross Stratejisini Uygulamak Istediginiz coini parite cifti ve uzantisiyle birlikte ismini giriniz. Orn : (BTCUSDT.csv)")
    okunacakCsv = input("Coini giriniz : ")

    df = pd.read_csv(okunacakCsv,names=basliklar) #Cekdigimiz verilere basliklar atıyoruz

    open = df['open']
    close = df['close']
    acilisZamani = df['opentime']
    high = df['high']
    low = df['low']

    sma50 = ta.ma("sma",close, lenght=50)
    sma200 = ta.ma("sma",close, length=200)
    print("##### GDCross Metod Active #####")
    for i in range(len(close)): #kapanis verilerini tek tek gezen dongu
        if pd.isna(sma50[i]) is False : #isna metodu icine koydugun degerler NaN ise True degilse False donduruyor
            if sma50[i-1] < sma200[i-1] and sma50[i] > sma200[i]: #Yukarı kesisim metodu sma50 sma200u yukarı yonde kestimi
                print(zamanHesapla(acilisZamani[i+1]),"tarihinde",cuzdan/close[i],"adet BTC alındı")
                print("##################")
                alimSayisi +=1
                toplamCoin=cuzdan/close[i]
                verilenKomisyon+= komisyonOrani*cuzdan
            if sma50[i-1] > sma200[i-1] and sma50[i] < sma200[i] and alimSayisi>0:#DEADCROSS #Asagi kesisim metodu sma50 sma200u asagi yonde kestimi
                print(zamanHesapla(acilisZamani[i+1]),"tarihinde",toplamCoin,"adet BTC satıldı")
                satimSayisi +=1
                fiyat = close[i]*toplamCoin
                cuzdan=fiyat
                toplamCoin=0
                verilenKomisyon+= komisyonOrani*fiyat
                print("Bu iki islem sonucundaki cuzdan bakiyesi : ",cuzdan)
                print("##################")

    print("Toplam Yapılan Islem : ",alimSayisi+satimSayisi)
    print("Toplam Verilen Komisyon : ", verilenKomisyon)
    print("Total Cuzdan Bakiyesi : ", cuzdan)


veriCekmeVeMatrikseUyarlama(sembolGir(), periyotGir(),zamanGir(0),zamanGir(1))
DCA()
gdCross()

