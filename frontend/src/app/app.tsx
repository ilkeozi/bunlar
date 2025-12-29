import { Routes, Route } from 'react-router-dom';
import { SiteHeader } from './components/SiteHeader';
import { HomePage } from './pages/HomePage';
import { ChemistryPage } from './pages/subjects/chemistry/ChemistryPage';
import { BohrModelPage } from './pages/subjects/chemistry/BohrModelPage';
import { DaltonModelPage } from './pages/subjects/chemistry/DaltonModelPage';
import { BiologyPage } from './pages/BiologyPage';
import { PhysicsPage } from './pages/PhysicsPage';
import { MathematicsPage } from './pages/MathematicsPage';
import { AboutPage } from './pages/AboutPage';

export function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950/95 to-slate-900 text-foreground">
      <SiteHeader />
      <main className="mx-auto w-full max-w-[1200px] px-6 pb-12 pt-8 sm:px-8 lg:px-10">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/subjects/chemistry" element={<ChemistryPage />} />
          <Route path="/subjects/chemistry/bohr-atom-model" element={<BohrModelPage />} />
          <Route path="/subjects/chemistry/dalton-atom-model" element={<DaltonModelPage />} />
          <Route path="/subjects/biology" element={<BiologyPage />} />
          <Route path="/subjects/physics" element={<PhysicsPage />} />
          <Route path="/subjects/mathematics" element={<MathematicsPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
