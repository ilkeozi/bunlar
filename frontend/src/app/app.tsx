import { Routes, Route } from 'react-router-dom';
import { SiteHeader } from './components/SiteHeader';
import { HomePage } from './pages/HomePage';
import { ChemistryPage } from './pages/subjects/chemistry/ChemistryPage';
import { BohrModelPage } from './pages/subjects/chemistry/BohrModelPage';
import { DaltonModelPage } from './pages/subjects/chemistry/DaltonModelPage';
import { ThomsonModelPage } from './pages/subjects/chemistry/ThomsonModelPage';
import { RutherfordModelPage } from './pages/subjects/chemistry/RutherfordModelPage';
import { ClimateTechPage } from './pages/ClimateTechPage';
import { BiologyPage } from './pages/BiologyPage';
import { PhysicsPage } from './pages/PhysicsPage';
import { MathematicsPage } from './pages/MathematicsPage';
import { AboutPage } from './pages/AboutPage';
import { ArticlesPage } from './pages/ArticlesPage';
import { CarbonAwareMotorAssemblyPage } from './pages/subjects/climate-tech/CarbonAwareMotorAssemblyPage';

export function App() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950/95 to-slate-900 text-foreground">
      <SiteHeader />
      <main className="mx-auto w-full max-w-[1200px] px-6 pb-12 pt-8 sm:px-8 lg:px-10">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/articles" element={<ArticlesPage />} />
          <Route path="/subjects/chemistry" element={<ChemistryPage />} />
          <Route path="/subjects/chemistry/bohr-atom-model" element={<BohrModelPage />} />
          <Route path="/subjects/chemistry/dalton-atom-model" element={<DaltonModelPage />} />
          <Route path="/subjects/chemistry/thomson-atom-model" element={<ThomsonModelPage />} />
          <Route path="/subjects/chemistry/rutherford-atom-model" element={<RutherfordModelPage />} />
          <Route path="/subjects/climate-tech" element={<ClimateTechPage />} />
          <Route
            path="/subjects/climate-tech/carbon-aware-motor-assembly"
            element={<CarbonAwareMotorAssemblyPage />}
          />
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
