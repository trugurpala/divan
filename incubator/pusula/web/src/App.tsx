import { useHandleSignInCallback, useLogto } from '@logto/react';
import { useState } from 'react';

type Props = {
  apiResource: string;
};

function Callback() {
  const { isLoading } = useHandleSignInCallback(() => {
    window.location.replace('/');
  });

  return <main className="centered">{isLoading ? 'Oturum açılıyor…' : 'Yönlendiriliyor…'}</main>;
}

function Dashboard({ apiResource }: Props) {
  const { isAuthenticated, isLoading, signIn, signOut, getAccessToken } = useLogto();
  const [teamId, setTeamId] = useState('');
  const [result, setResult] = useState('');
  const [requesting, setRequesting] = useState(false);

  const callbackUri = `${window.location.origin}/callback`;

  async function loadMembership() {
    if (!teamId.trim()) {
      setResult('Takım kimliği gerekli.');
      return;
    }

    setRequesting(true);
    setResult('');

    try {
      const token = await getAccessToken(apiResource);
      if (!token) {
        throw new Error('API erişim tokenı alınamadı.');
      }

      const response = await fetch(`/api/teams/${encodeURIComponent(teamId.trim())}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const body = (await response.json()) as unknown;
      setResult(JSON.stringify({ status: response.status, body }, null, 2));
    } catch (error) {
      setResult(error instanceof Error ? error.message : 'Bilinmeyen istek hatası.');
    } finally {
      setRequesting(false);
    }
  }

  if (isLoading) {
    return <main className="centered">Kimlik durumu okunuyor…</main>;
  }

  if (!isAuthenticated) {
    return (
      <main className="centered panel">
        <p className="eyebrow">Divan Pusula</p>
        <h1>Yazılım üretim kontrol merkezi</h1>
        <p>Mizan karar verir, ajanlar önerir, kanıt olmadan işlem ilerlemez.</p>
        <button type="button" onClick={() => void signIn(callbackUri)}>
          Giriş yap
        </button>
      </main>
    );
  }

  return (
    <main className="shell">
      <header>
        <div>
          <p className="eyebrow">Divan Pusula</p>
          <h1>Ana Sayfa</h1>
        </div>
        <button type="button" className="secondary" onClick={() => void signOut(window.location.origin)}>
          Çıkış yap
        </button>
      </header>

      <nav aria-label="Ana menü">
        {['Ana Sayfa', 'Projeler', 'İşler', 'Hafıza', 'Yayınlar', 'Ayarlar'].map((item) => (
          <span key={item}>{item}</span>
        ))}
      </nav>

      <section className="panel">
        <h2>Tenant erişim kanıtı</h2>
        <p>Takım kimliği ile Django API’deki gerçek üyelik guard’ını çağırır.</p>
        <label>
          Takım UUID
          <input value={teamId} onChange={(event) => setTeamId(event.target.value)} placeholder="00000000-…" />
        </label>
        <button type="button" disabled={requesting} onClick={() => void loadMembership()}>
          {requesting ? 'Kontrol ediliyor…' : 'Üyeliğimi kontrol et'}
        </button>
        {result ? <pre>{result}</pre> : null}
      </section>
    </main>
  );
}

export function App(props: Props) {
  if (window.location.pathname === '/callback') {
    return <Callback />;
  }

  return <Dashboard {...props} />;
}
