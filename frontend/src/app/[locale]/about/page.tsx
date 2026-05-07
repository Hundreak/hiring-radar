import {MarketingPageShell} from '@/components/marketing/page-shell';
import {SectionHeading} from '@/components/marketing/section-heading';

export default async function AboutPage({
  params
}: {
  params: Promise<{locale: string}>;
}) {
  const {locale} = await params;

  return (
    <MarketingPageShell locale={locale}>
      <section className="container-shell py-20">
        <SectionHeading
          eyebrow="Hakkımızda"
          title="NoyTera, kariyer kararlarını daha net ve daha sistematik hale getirmek için inşa edildi."
          description="Biz bir ilan listesi sunmaktan daha fazlasını hedefliyoruz. NoyTera; adayların kendilerini daha doğru ifade edebildiği, iş piyasasını daha anlamlı okuyabildiği ve daha güçlü fırsatlara daha bilinçli şekilde ilerleyebildiği bir kariyer altyapısıdır."
        />

        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <div className="rounded-[28px] border border-white/10 bg-[#171717] p-8">
            <h2 className="text-2xl font-semibold text-white">Ne inşa ediyoruz?</h2>
            <p className="mt-5 text-base leading-8 text-white/68">
              NoyTera; aday profillerini yapılandıran, CV içeriğini anlamlandıran,
              eksik sinyalleri görünür hale getiren ve çoklu platformlardan gelen ilanları
              tek karar yüzeyinde toplayan modern bir kariyer ürünüdür. Amacımız,
              iş arama deneyimini yalnızca “daha hızlı” değil, aynı zamanda daha
              açıklanabilir, daha kaliteli ve daha stratejik hale getirmektir.
            </p>
            <p className="mt-5 text-base leading-8 text-white/68">
              Ürün yaklaşımımız; profil zekâsı, eşleşme kalitesi, kullanıcı güveni ve
              kurumsal tasarım disiplini üzerine kuruludur. Adayların iş arama
              yolculuğunda maruz kaldığı dağınıklığı azaltmak, doğru fırsatları
              görünür kılmak ve karar kalitesini artırmak bizim için temel ürün
              problemidir.
            </p>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-[#171717] p-8">
            <h2 className="text-2xl font-semibold text-white">Neden varız?</h2>
            <p className="mt-5 text-base leading-8 text-white/68">
              Bugünün aday deneyimi çoğu zaman parçalıdır. Farklı iş platformları,
              tutarsız profil sinyalleri, belirsiz eşleşme mantıkları ve düşük
              açıklanabilirlik; iş arama sürecini yorucu hale getirir. Kullanıcılar
              hangi ilanın gerçekten uygun olduğunu, hangi bilgi eksikliğinin onları
              geride bıraktığını ve nereden başlamaları gerektiğini net biçimde
              göremeyebilir.
            </p>
            <p className="mt-5 text-base leading-8 text-white/68">
              NoyTera bu sorunu çözmek için var. Kariyer ekosistemini; veri kalitesi,
              güven, sadelik ve yüksek ürün standardı ile yeniden yorumluyoruz.
              Uzun vadede hedefimiz, adaylar için yalnızca iyi görünen değil; gerçekten
              karar kalitesini artıran bir kariyer işletim sistemi inşa etmektir.
            </p>
          </div>
        </div>

        <div className="mt-6 rounded-[32px] border border-white/10 bg-[#151515] p-8 md:p-10">
          <h2 className="text-3xl font-semibold tracking-tight text-white">Vizyonumuz</h2>
          <p className="mt-6 max-w-4xl text-lg leading-8 text-white/68">
            NoyTera’i, adayların kendilerini daha iyi tanıdığı, profillerini daha güçlü
            sunduğu ve iş piyasasında gürültü yerine sinyal odaklı ilerlediği yeni nesil
            bir kariyer altyapısı olarak konumluyoruz. Bu nedenle ürünümüzü yalnızca ilan
            keşif aracı gibi değil; profil kalitesini artıran, karar desteği sağlayan,
            yapay zeka ile strateji geliştiren ve güvenli veri yönetimini ciddiyetle ele
            alan bütünleşik bir platform olarak geliştiriyoruz.
          </p>
        </div>
      </section>
    </MarketingPageShell>
  );
}