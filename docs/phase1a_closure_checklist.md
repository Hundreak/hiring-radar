# Phase 1A Closure Checklist

Bu doküman, Phase 1A kapanışı öncesi manuel doğrulama adımlarını standardize eder.

## 1. Profil aggregate ve section CRUD
- [ ] Profil sayfası açıldığında veriler aggregate response ile doluyor.
- [ ] Temel Bilgiler alanı kaydedildikten sonra sayfa tam refresh istemeden güncelleniyor.
- [ ] Hedefler ve Tercihler alanı kaydedildikten sonra kart görünümü doğru yenileniyor.
- [ ] Deneyim ekleme, düzenleme ve silme akışları çalışıyor.
- [ ] Eğitim ekleme, düzenleme ve silme akışları çalışıyor.
- [ ] Dil ekleme, düzenleme ve silme akışları çalışıyor.
- [ ] Beceri ekleme, düzenleme ve silme akışları çalışıyor.

## 2. Replace-style CRUD güvenliği
- [ ] Bir section create/update/delete sonrası ekran stale kalmıyor.
- [ ] Başka bir section işleminden sonra henüz kaydedilmemiş Temel Bilgiler taslağı silinmiyor.
- [ ] Mutation sonrası yanlış item edit ekranı açılmıyor.

## 3. CV workspace akışları
- [ ] CV yükleme başarıyla tamamlanıyor.
- [ ] CV yüklendikten sonra workspace summary güncelleniyor.
- [ ] CV apply sonrası aggregate refresh tetikleniyor.
- [ ] CV apply başarılı ama refresh başarısız olursa kullanıcı net bir uyarı görüyor.
- [ ] CV Sağlığı drawer içeriği açılıp okunabiliyor.

## 4. Avatar akışları
- [ ] Profil fotoğrafı seçilebiliyor.
- [ ] Crop/konumlandırma düzgün çalışıyor.
- [ ] Kaydedilen avatar profil kartında doğru görünüyor.
- [ ] Kaydedilen avatar sağ üst kullanıcı menüsünde de güncelleniyor.
- [ ] Beyaz boşluk, yanlış crop veya yan çizgi problemi görünmüyor.

## 5. Belge ve kanıt yükleme
- [ ] Dil sertifikası seçilebiliyor ve kaydedilebiliyor.
- [ ] Sertifika upload başarısız olursa dil kaydı tamamen kaybolmuyor.
- [ ] Beceri kanıt dosyası seçilebiliyor ve kaydedilebiliyor.
- [ ] Beceri kanıt upload başarısız olursa beceri kaydı tamamen kaybolmuyor.

## 6. Menü ve çıkış yap
- [ ] Sağ üst kullanıcı menüsü açılıyor.
- [ ] Profil, Güvenlik, Tercihler ve Bildirimler yönlendirmeleri çalışıyor.
- [ ] Çıkış Yap hem menüden hem Bildirimler ekranından çalışıyor.
- [ ] Logout sırasında çift tıklama/bozuk loading davranışı yok.

## 7. Kullanıcı-facing yüzey
- [ ] Ham backend etiketleri görünmüyor.
- [ ] `window.confirm` benzeri browser confirm diyalogları görünmüyor.
- [ ] Başarı/hata/uyarı mesajları ortak banner diliyle gösteriliyor.
- [ ] Profil workspace masaüstünde dar/sıkışık görünmüyor.
- [ ] Kritik alanlarda bariz responsive taşma yok.

## Kapanış kararı
Aşağıdaki koşullar aynı anda sağlanmadan Phase 1A kapanmış sayılmamalı:
- Otomatik regression harness geçti.
- Manuel checklist tamamlandı.
- Kritik profile/CV/avatar/logout akışlarında bloklayıcı hata kalmadı.
