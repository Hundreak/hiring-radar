'use client';

import {
  Bell,
  Building2,
  CreditCard,
  Globe,
  Lock,
  Palette,
  Save,
  Shield,
  Users,
} from 'lucide-react';
import {useState} from 'react';

import {Button} from '@/components/ui/button';
import {cn} from '@/lib/utils';

function SettingsSection({title, description, icon: Icon, children}: {
  title: string; description: string; icon: React.ElementType; children: React.ReactNode;
}) {
  return (
    <div className="surface-card p-6">
      <div className="flex items-center gap-3 mb-5">
        <div className="flex size-10 items-center justify-center rounded-2xl bg-secondary text-secondary-foreground">
          <Icon className="size-5" />
        </div>
        <div>
          <h2 className="text-sm font-bold">{title}</h2>
          <p className="text-xs text-muted-foreground">{description}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

export default function EmployerSettingsPage() {
  const [companyName, setCompanyName] = useState('NoyTera A.Ş.');
  const [email, setEmail] = useState('hr@noytera.com');
  const [notifyNewApp, setNotifyNewApp] = useState(true);
  const [notifyMatch, setNotifyMatch] = useState(true);
  const [notifyWeekly, setNotifyWeekly] = useState(false);

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="employer-page-title">Ayarlar</h1>
        <p className="employer-page-desc">Şirket bilgileri ve bildirim tercihlerini yönetin</p>
      </div>

      {/* Company Profile */}
      <SettingsSection
        title="Şirket Profili"
        description="Şirket bilgilerinizi güncelleyin"
        icon={Building2}
      >
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Şirket Adı</label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="h-10 w-full max-w-md rounded-2xl border border-border bg-surface px-4 text-sm text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1.5">İletişim E-postası</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-10 w-full max-w-md rounded-2xl border border-border bg-surface px-4 text-sm text-foreground focus:outline-none focus:ring-4 focus:ring-[var(--ring)]"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-muted-foreground mb-1.5">Şirket Logosu</label>
            <div className="flex items-center gap-4">
              <div className="flex size-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-accent text-lg font-bold text-white">
                NT
              </div>
              <Button size="sm" variant="secondary">Değiştir</Button>
            </div>
          </div>
        </div>
      </SettingsSection>

      {/* Notifications */}
      <SettingsSection
        title="Bildirim Tercihleri"
        description="Hangi olaylar hakkında bildirim almak istediğinizi seçin"
        icon={Bell}
      >
        <div className="space-y-3">
          {[
            {label: 'Yeni başvuru bildirimleri', desc: 'Her yeni aday başvurusunda e-posta al', checked: notifyNewApp, onChange: () => setNotifyNewApp(!notifyNewApp)},
            {label: 'Yüksek eşleşme uyarıları', desc: 'Eşleşme skoru 90+ olan adaylar için bildirim', checked: notifyMatch, onChange: () => setNotifyMatch(!notifyMatch)},
            {label: 'Haftalık özet', desc: 'Her Pazartesi haftalık performans özeti', checked: notifyWeekly, onChange: () => setNotifyWeekly(!notifyWeekly)},
          ].map((item) => (
            <label key={item.label} className="flex items-start gap-3 p-3 rounded-xl border border-border bg-surface-muted cursor-pointer transition hover:border-border-strong">
              <input
                type="checkbox"
                checked={item.checked}
                onChange={item.onChange}
                className="size-5 mt-0.5 accent-primary rounded"
              />
              <div>
                <div className="text-sm font-semibold">{item.label}</div>
                <div className="text-xs text-muted-foreground">{item.desc}</div>
              </div>
            </label>
          ))}
        </div>
      </SettingsSection>

      {/* Security */}
      <SettingsSection
        title="Güvenlik"
        description="Hesap güvenliği ayarları"
        icon={Shield}
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-surface-muted">
            <div className="flex items-center gap-3">
              <Lock className="size-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-semibold">Şifre Değiştir</div>
                <div className="text-xs text-muted-foreground">Son değişiklik: 30 gün önce</div>
              </div>
            </div>
            <Button size="sm" variant="secondary">Değiştir</Button>
          </div>
          <div className="flex items-center justify-between p-3 rounded-xl border border-border bg-surface-muted">
            <div className="flex items-center gap-3">
              <Users className="size-4 text-muted-foreground" />
              <div>
                <div className="text-sm font-semibold">Takım Üyeleri</div>
                <div className="text-xs text-muted-foreground">3 aktif kullanıcı</div>
              </div>
            </div>
            <Button size="sm" variant="secondary">Yönet</Button>
          </div>
        </div>
      </SettingsSection>

      {/* Save */}
      <div className="flex justify-end">
        <Button>
          <Save className="size-4 mr-2" />
          Ayarları Kaydet
        </Button>
      </div>
    </div>
  );
}
