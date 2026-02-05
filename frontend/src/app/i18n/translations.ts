export const TRANSLATIONS = {
  en: {
    'app.title': 'bunlar',
    'app.subtitle': 'things that cross my mind',
    'app.language': 'Language',
    'nav.home': 'Home',
    'nav.visualizations': 'Visualizations',
    'nav.tools': 'Tools',
    'nav.articles': 'Articles',
    'nav.about': 'About',
    'nav.openMenu': 'Open navigation',
    'visualizations.title': 'Visualizations',
    'visualizations.subtitle':
      'Interactive modules and experiments, all in one place.',
    'visualizations.filter.all': 'All',
    'home.featured.title': 'Featured visualization',
    'visualizations.back': 'Visualizations',
    'subjects.chemistry.title': 'Chemistry',
    'subjects.chemistry.subtitle':
      'Explore atomic structure and electron shells in 3D.',
    'subjects.biology.title': 'Biology',
    'subjects.physics.title': 'Physics',
    'subjects.mathematics.title': 'Mathematics',
    'subjects.climateTech.title': 'Climate Tech',
    'subjects.tools.title': 'Tools',
    'subjects.climateTech.subtitle':
      'Explore product carbon footprint insights through interactive assemblies.',
    'subjects.tools.subtitle': 'Utilities for CAD conversions and analysis.',
    'subjects.biology.placeholder':
      "Coming soon. We'll add interactive biology modules here.",
    'subjects.physics.placeholder':
      "Coming soon. We'll add interactive physics modules here.",
    'subjects.mathematics.placeholder':
      "Coming soon. We'll add interactive mathematics modules here.",
    'subjects.climateTech.placeholder':
      'Coming soon. Explore product carbon footprint with interactive 3D assemblies.',
    'climateTech.modules.carbonAware.title':
      'Carbon Aware Planetary Gearbox Assembly',
    'climateTech.modules.carbonAware.description':
      'Inspect component level product carbon footprint signals in an exploded 3D assembly.',
    'climateTech.modules.carbonAware.cta': 'Open visualization',
    'climateTech.modules.carbonAware.placeholder':
      'Prototype loaded. Product carbon footprint overlays, inspection, and exploded view are next.',
    'climateTech.modules.assemblyViewer.title': 'Assembly Hierarchy Explorer',
    'climateTech.modules.assemblyViewer.description':
      'Load a CAD assembly and review its hierarchy with a live 3D view.',
    'climateTech.modules.assemblyViewer.cta': 'Open visualization',
    'assemblyViewer.input.title': 'Input File',
    'assemblyViewer.input.description':
      'Upload a STEP or IGES file to load the model and generate metadata.',
    'assemblyViewer.input.label': 'Choose File',
    'assemblyViewer.input.placeholder': 'No file selected.',
    'assemblyViewer.input.hint': 'Accepted: .step, .stp, .iges, .igs',
    'assemblyViewer.input.sample': 'Clear selection',
    'assemblyViewer.status.idle': 'Waiting for a file.',
    'assemblyViewer.status.converting': 'Converting CAD...',
    'assemblyViewer.status.loading': 'Loading model...',
    'assemblyViewer.status.ready': 'Model ready.',
    'assemblyViewer.status.error': 'Model failed to load.',
    'assemblyViewer.status.unsupported':
      'Unsupported file type. Use STEP or IGES.',
    'assemblyViewer.status.conversionFailed':
      'Conversion failed. Please try a different file.',
    'assemblyViewer.status.metadataMismatch':
      'Metadata does not match the generated node map.',
    'assemblyViewer.controls.title': 'Viewer Controls',
    'assemblyViewer.controls.autoRotate': 'Auto Rotate',
    'assemblyViewer.controls.autoRotateHint':
      'Keep the model moving to spot assembly details.',
    'assemblyViewer.controls.resetView': 'Reset View',
    'assemblyViewer.stats.title': 'Model Stats',
    'assemblyViewer.stats.nodes': 'Nodes',
    'assemblyViewer.stats.meshes': 'Meshes',
    'articles.title': 'Articles',
    'articles.placeholder':
      "Coming soon. We'll publish articles that link to the visualizations.",
    'chemistry.modules.bohrModel.title': 'Bohr Atom Model',
    'chemistry.modules.bohrModel.description':
      'Visualize electron shells using the Bohr model.',
    'chemistry.modules.bohrModel.cta': 'Open model',
    'chemistry.modules.bohrModel.badge.ib': 'IB',
    'chemistry.modules.bohrModel.badge.structure': 'Structure 1',
    'chemistry.modules.daltonModel.title': 'Dalton Atom Model',
    'chemistry.modules.daltonModel.description':
      "See the atom as a solid sphere in Dalton's model.",
    'chemistry.modules.daltonModel.cta': 'Open model',
    'chemistry.modules.daltonModel.badge.ib': 'IB',
    'chemistry.modules.daltonModel.badge.structure': 'Structure 1',
    'chemistry.modules.thomsonModel.title': 'Thomson Atom Model',
    'chemistry.modules.thomsonModel.description':
      'Explore the plum pudding model with embedded electrons.',
    'chemistry.modules.thomsonModel.cta': 'Open model',
    'chemistry.modules.thomsonModel.badge.ib': 'IB',
    'chemistry.modules.thomsonModel.badge.structure': 'Structure 1',
    'chemistry.modules.rutherfordModel.title': 'Rutherford Atom Model',
    'chemistry.modules.rutherfordModel.description':
      'See a dense nucleus with electrons in planetary orbits.',
    'chemistry.modules.rutherfordModel.cta': 'Open model',
    'chemistry.modules.rutherfordModel.badge.ib': 'IB',
    'chemistry.modules.rutherfordModel.badge.structure': 'Structure 1',
    'chemistry.modules.more.title': 'More chemistry modules',
    'chemistry.modules.more.description': 'Coming soon.',
    'chemistry.modules.more.note':
      'Add experiments, reactions, and bonding lessons here.',
    'modules.more.title': 'More visualizations',
    'modules.more.description': 'Coming soon.',
    'modules.more.note': 'Add more visualizations here as you build them.',
    'tools.stepConverter.title': 'STEP / IGES Converter',
    'tools.stepConverter.subtitle':
      'Convert CAD files to glTF, GLB, or OBJ with OpenCascade.',
    'tools.stepConverter.description':
      'Upload STEP or IGES files and receive web-ready exports.',
    'tools.stepConverter.cta': 'Open converter',
    'tools.stepConverter.badge': 'Experimental',
    'tools.stepConverter.panel.title': 'Convert a file',
    'tools.stepConverter.panel.description':
      'Upload a STEP/IGES file and choose an output format. Large models can take a few minutes.',
    'tools.stepConverter.form.fileLabel': 'Input file',
    'tools.stepConverter.form.fileHint': 'Accepted: .step, .stp (max 15 MB)',
    'tools.stepConverter.form.filePlaceholder': 'Choose a file',
    'tools.stepConverter.form.modeLabel': 'Conversion mode',
    'tools.stepConverter.form.modeBasic': 'Basic',
    'tools.stepConverter.form.modeAdvanced': 'Advanced',
    'tools.stepConverter.form.formatLabel': 'Output format',
    'tools.stepConverter.form.outputLabel': 'Output',
    'tools.stepConverter.form.outputBundle':
      'ZIP bundle (.glb + .metadata.json)',
    'tools.stepConverter.form.linDeflection': 'Linear deflection',
    'tools.stepConverter.form.angDeflection': 'Angular deflection',
    'tools.stepConverter.form.relative': 'Relative deflection',
    'tools.stepConverter.form.parallel': 'Parallel triangulation',
    'tools.stepConverter.form.includeBom': 'Include BOM export',
    'tools.stepConverter.form.includeNodeMap': 'Include node map',
    'tools.stepConverter.form.submit': 'Convert now',
    'tools.stepConverter.form.reset': 'Clear',
    'tools.stepConverter.form.cancel': 'Cancel',
    'tools.stepConverter.status.idle': 'Ready to convert.',
    'tools.stepConverter.status.loading': 'Converting...',
    'tools.stepConverter.status.stage.parsing': 'Parsing STEP...',
    'tools.stepConverter.status.stage.meshing': 'Meshing geometry...',
    'tools.stepConverter.status.stage.writing': 'Writing GLB...',
    'tools.stepConverter.status.stage.metadata': 'Building metadata...',
    'tools.stepConverter.status.stage.packaging': 'Packaging bundle...',
    'tools.stepConverter.status.success': 'Conversion complete.',
    'tools.stepConverter.status.error': 'Conversion failed.',
    'tools.stepConverter.status.metadataLoading': 'Generating metadata...',
    'tools.stepConverter.status.metadataSuccess': 'Metadata ready.',
    'tools.stepConverter.status.metadataError': 'Metadata failed.',
    'tools.stepConverter.status.apiUnavailable':
      'Converter API is unreachable. Please try again.',
    'tools.stepConverter.status.timeout':
      'Conversion timed out. Please try again.',
    'tools.stepConverter.status.missingFile':
      'Select a STEP or IGES file first.',
    'tools.stepConverter.status.invalidNumbers':
      'Deflection values must be numbers.',
    'tools.stepConverter.error.FILE_TOO_LARGE':
      'File is too large. Maximum size is 15 MB.',
    'tools.stepConverter.error.UNSUPPORTED_EXTENSION':
      'Unsupported file type. Please choose a .step or .stp file.',
    'tools.stepConverter.error.INVALID_STEP':
      'This STEP file looks invalid or corrupt. Try a different export.',
    'tools.stepConverter.error.UNSUPPORTED_STEP_CONTENT':
      'This STEP file contains no supported solids/assemblies.',
    'tools.stepConverter.error.UNITS_SCALE_MISMATCH':
      'Units scale looks off (possible mm vs m mismatch). Try a different export.',
    'tools.stepConverter.error.WASM_LOAD_FAILED':
      'Conversion engine failed to load. Please refresh and try again.',
    'tools.stepConverter.error.OUT_OF_MEMORY':
      'Conversion ran out of memory. Try a smaller model or fewer details.',
    'tools.stepConverter.error.CONVERSION_FAILED':
      'Conversion failed. Please try again.',
    'tools.stepConverter.error.METADATA_FAILED':
      'Metadata generation failed for this file.',
    'tools.stepConverter.error.GLB_PATCH_FAILED':
      'Failed to embed metadata into the GLB output.',
    'tools.stepConverter.error.ZIP_FAILED':
      'Failed to package outputs into a zip bundle.',
    'tools.stepConverter.output.label': 'Download',
    'tools.stepConverter.output.cta': 'Download bundle',
    'tools.stepConverter.output.metadataLabel': 'Metadata exports',
    'tools.stepConverter.output.bomCta': 'Download BOM JSON',
    'tools.stepConverter.output.nodeMapCta': 'Download node map JSON',
    'tools.stepConverterBrowser.title': 'STEP / IGES Converter',
    'tools.stepConverterBrowser.subtitle':
      'Convert CAD files to glTF, GLB, or OBJ with OpenCascade.',
    'tools.stepConverterBrowser.description':
      'Upload STEP or IGES files and receive web-ready exports.',
    'tools.stepConverterBrowser.cta': 'Open converter',
    'tools.stepConverterBrowser.badge': 'Experimental',
    'bohrModel.title': 'Bohr Atom Model',
    'bohrModel.subtitle': 'Visualize electron shells using the Bohr model.',
    'bohrModel.card.title': 'Explorer',
    'bohrModel.card.description':
      'Pick an element to update the visualization in real time.',
    'daltonModel.title': 'Dalton Atom Model',
    'daltonModel.subtitle': "Explore Dalton's solid-sphere model of the atom.",
    'daltonModel.card.title': 'Explorer',
    'daltonModel.card.description':
      'Pick an element to update the visualization in real time.',
    'thomsonModel.title': 'Thomson Atom Model',
    'thomsonModel.subtitle':
      'See electrons embedded in a positively charged sphere.',
    'thomsonModel.card.title': 'Explorer',
    'thomsonModel.card.description':
      'Pick an element to update the visualization in real time.',
    'rutherfordModel.title': 'Rutherford Atom Model',
    'rutherfordModel.subtitle':
      'Explore the nuclear model with electrons orbiting a dense center.',
    'rutherfordModel.card.title': 'Explorer',
    'rutherfordModel.card.description':
      'Pick an element to update the visualization in real time.',
    'about.title': 'About the Explorer',
    'about.paragraph1':
      'The Science Explorer is a portfolio-ready playground that blends real-time graphics with approachable lesson content. Use it to showcase interactive storytelling, React architecture, and thoughtful UX for STEM topics.',
    'about.paragraph2':
      'Built with Vite, React, Zustand, and tailored components from shadcn/ui, the project highlights clean composable patterns, state synchronisation, and immersive visuals powered by three.js.',
    'legend.proton': 'Proton',
    'legend.neutron': 'Neutron',
    'legend.electron': 'Electron',
    'legend.positiveSphere': 'Positive sphere',
    'element.label': 'Element',
    'stats.atomicNumber': 'Atomic number',
    'stats.atomicMass': 'Atomic mass',
    'stats.protons': 'Protons',
    'stats.neutrons': 'Neutrons',
    'stats.electrons': 'Electrons',
    'stats.category': 'Category',
    'stats.shells': 'Electron shells',
    'controls.autoRotate': 'Auto rotate camera',
    'controls.freezeMotion': 'Freeze motion',
    'controls.rotateAtom': 'Rotate atom',
    'controls.tiltedOrbits': 'Tilt electron orbits',
    'controls.showPositiveSphere': 'Show positive sphere',
    'controls.cutawaySphere': 'Cutaway sphere',
    'controls.showTrails': 'Show electron trails',
    'controls.explode': 'Explode view',
    'controls.partsDetected': 'Parts detected',
    'controls.explodeHintSingle': 'Explode needs multiple parts.',
    'controls.modelHierarchyTitle': 'Model hierarchy',
    'controls.modelHierarchyDescription': 'List of nodes detected in the GLB.',
    'controls.modelHierarchyEmpty': 'No hierarchy data yet.',
    'controls.partGroupsTitle': 'Unique parts',
    'controls.partGroupsDescription': 'Grouped by normalized mesh names.',
    'controls.partGroupsEmpty': 'No part groups detected.',
    'controls.partGroupsTopAssembly': 'Top assembly:',
    'controls.assemblyGroupsTitle': 'Sub-assemblies',
    'controls.assemblyGroupsDescription': 'Named groups with mesh children.',
    'controls.assemblyGroupsEmpty': 'No sub-assemblies detected.',
    'controls.debugMaterials': 'Debug materials',
    'controls.pcfOverlay': 'Carbon footprint overlay',
    'controls.pcfOverlayMode': 'Overlay mode',
    'controls.pcfOverlayNone': 'None',
    'controls.pcfOverlayTotal': 'Total footprint',
    'controls.pcfOverlayMaterial': 'Material',
    'controls.pcfOverlayManufacturing': 'Manufacturing',
    'controls.pcfOverlayTransport': 'Transport',
    'controls.pcfLegendLow': 'Low',
    'controls.pcfLegendHigh': 'High',
    'controls.pcfLegendUnit': 'kg CO2e',
    'controls.pcfLegendMaterial': 'Material',
    'controls.pcfLegendManufacturing': 'Manufacturing',
    'controls.pcfLegendTransport': 'Transport',
    'controls.viewTitle': 'View controls',
    'controls.orbitPan': 'Enable panning',
    'controls.lockVerticalTilt': 'Lock vertical tilt',
    'controls.resetView': 'Reset view',
    'controls.enterTheater': 'Enter theater mode',
    'controls.exitTheater': 'Exit theater mode',
    'controls.showControls': 'Show controls',
    'controls.hideControls': 'Hide controls',
    'climateTech.tooltip.materialLabel': 'Material',
    'climateTech.tooltip.categoryLabel': 'Category',
    'climateTech.tooltip.massLabel': 'Mass',
    'climateTech.tooltip.partNumberLabel': 'Part number',
    'climateTech.tooltip.sourcingSection': 'Sourcing',
    'climateTech.tooltip.sourcingLabel': 'Sourcing',
    'climateTech.tooltip.sourcingManufactured': 'In-house',
    'climateTech.tooltip.sourcingSupplier': 'Supplier',
    'climateTech.tooltip.supplierLabel': 'Supplier',
    'climateTech.tooltip.plantLabel': 'Plant',
    'climateTech.tooltip.originLabel': 'Origin',
    'climateTech.tooltip.materialSection': 'Material',
    'climateTech.tooltip.co2eBreakdown': 'CO2e breakdown',
    'climateTech.tooltip.unknownPart': 'Unknown part',
    'climateTech.tooltip.unknownValue': 'Unknown',
    'units.kg': 'kg',
    'category.Nonmetal': 'Nonmetal',
    'category.Noble gas': 'Noble gas',
    'category.Alkali metal': 'Alkali metal',
    'category.Alkaline earth metal': 'Alkaline earth metal',
    'category.Metalloid': 'Metalloid',
    'category.Halogen': 'Halogen',
    'category.Post-transition metal': 'Post-transition metal',
    'category.Transition metal': 'Transition metal',
    'category.Lanthanide': 'Lanthanide',
    'category.Actinide': 'Actinide',
  },
  tr: {
    'app.title': 'bunlar',
    'app.subtitle': 'aklımdan geçenler',
    'app.language': 'Dil',
    'nav.home': 'Ana Sayfa',
    'nav.visualizations': 'Görselleştirmeler',
    'nav.tools': 'Araçlar',
    'nav.articles': 'Yazılar',
    'nav.about': 'Hakkında',
    'nav.openMenu': 'Menüyü aç',
    'visualizations.title': 'Görselleştirmeler',
    'visualizations.subtitle': 'Etkileşimli modüller ve deneyler tek yerde.',
    'visualizations.filter.all': 'Tümü',
    'home.featured.title': 'Öne çıkan görselleştirme',
    'visualizations.back': 'Görselleştirmeler',
    'subjects.chemistry.title': 'Kimya',
    'subjects.chemistry.subtitle':
      'Atom yapısını ve elektron katmanlarını 3B olarak inceleyin.',
    'subjects.biology.title': 'Biyoloji',
    'subjects.physics.title': 'Fizik',
    'subjects.mathematics.title': 'Matematik',
    'subjects.climateTech.title': 'İklim Teknolojisi',
    'subjects.tools.title': 'Araçlar',
    'subjects.climateTech.subtitle':
      'Ürün karbon ayak izi içgörülerini etkileşimli montajlarla keşfedin.',
    'subjects.tools.subtitle': 'CAD dönüştürme ve analiz araçları.',
    'subjects.biology.placeholder':
      'Yakında. Etkileşimli biyoloji modülleri buraya eklenecek.',
    'subjects.physics.placeholder':
      'Yakında. Etkileşimli fizik modülleri buraya eklenecek.',
    'subjects.mathematics.placeholder':
      'Yakında. Etkileşimli matematik modülleri buraya eklenecek.',
    'subjects.climateTech.placeholder':
      'Yakında. Ürün karbon ayak izi odaklı 3B montaj görselleştirmeleri gelecek.',
    'climateTech.modules.carbonAware.title':
      'Karbon Duyarlı Planet Dişli Kutusu Montajı',
    'climateTech.modules.carbonAware.description':
      'Bileşen düzeyinde ürün karbon ayak izi göstergelerini 3B patlatılmış montajda inceleyin.',
    'climateTech.modules.carbonAware.cta': 'Görselleştirmeyi aç',
    'climateTech.modules.carbonAware.placeholder':
      'Prototip hazır. Ürün karbon ayak izi katmanları, inceleme ve patlatılmış görünüm yakında.',
    'climateTech.modules.assemblyViewer.title': 'Montaj Hiyerarşi Gezgini',
    'climateTech.modules.assemblyViewer.description':
      'Bir CAD montajı yükleyin ve hiyerarşiyi canlı 3B görünümle inceleyin.',
    'climateTech.modules.assemblyViewer.cta': 'Görselleştirmeyi aç',
    'assemblyViewer.input.title': 'Girdi dosyası',
    'assemblyViewer.input.description':
      'STEP veya IGES dosyası yükleyin; model ve metadata otomatik oluşur.',
    'assemblyViewer.input.label': 'Dosya seçin',
    'assemblyViewer.input.placeholder': 'Dosya seçilmedi.',
    'assemblyViewer.input.hint': 'Kabul edilenler: .step, .stp, .iges, .igs',
    'assemblyViewer.input.sample': 'Seçimi temizle',
    'assemblyViewer.status.idle': 'Dosya bekleniyor.',
    'assemblyViewer.status.converting': 'CAD dönüştürülüyor...',
    'assemblyViewer.status.loading': 'Model yükleniyor...',
    'assemblyViewer.status.ready': 'Model hazır.',
    'assemblyViewer.status.error': 'Model yüklenemedi.',
    'assemblyViewer.status.unsupported':
      'Desteklenmeyen dosya türü. STEP veya IGES kullanın.',
    'assemblyViewer.status.conversionFailed':
      'Dönüşüm başarısız. Başka bir dosya deneyin.',
    'assemblyViewer.status.metadataMismatch':
      'Metadata, oluşturulan düğüm haritasıyla eşleşmiyor.',
    'assemblyViewer.controls.title': 'Görüntüleyici kontrolleri',
    'assemblyViewer.controls.autoRotate': 'Otomatik döndür',
    'assemblyViewer.controls.autoRotateHint':
      'Montaj detaylarını görmek için modeli döndürmeye devam edin.',
    'assemblyViewer.controls.resetView': 'Görünümü sıfırla',
    'assemblyViewer.stats.title': 'Model istatistikleri',
    'assemblyViewer.stats.nodes': 'Düğümler',
    'assemblyViewer.stats.meshes': 'Mesh sayısı',
    'articles.title': 'Yazılar',
    'articles.placeholder':
      'Yakında. Görselleştirmelere bağlanan yazılar yayınlayacağız.',
    'chemistry.modules.bohrModel.title': 'Bohr Atom Modeli',
    'chemistry.modules.bohrModel.description':
      'Bohr modelini kullanarak elektron katmanlarını görselleştirin.',
    'chemistry.modules.bohrModel.cta': 'Modeli aç',
    'chemistry.modules.bohrModel.badge.ib': 'IB',
    'chemistry.modules.bohrModel.badge.structure': 'Yapı 1',
    'chemistry.modules.daltonModel.title': 'Dalton Atom Modeli',
    'chemistry.modules.daltonModel.description':
      'Dalton modelinde atomu katı bir küre olarak görün.',
    'chemistry.modules.daltonModel.cta': 'Modeli aç',
    'chemistry.modules.daltonModel.badge.ib': 'IB',
    'chemistry.modules.daltonModel.badge.structure': 'Yapı 1',
    'chemistry.modules.thomsonModel.title': 'Thomson Atom Modeli',
    'chemistry.modules.thomsonModel.description':
      'Elektronların gömülü olduğu erik pudingi modelini keşfedin.',
    'chemistry.modules.thomsonModel.cta': 'Modeli aç',
    'chemistry.modules.thomsonModel.badge.ib': 'IB',
    'chemistry.modules.thomsonModel.badge.structure': 'Yapı 1',
    'chemistry.modules.rutherfordModel.title': 'Rutherford Atom Modeli',
    'chemistry.modules.rutherfordModel.description':
      'Yoğun bir çekirdek ve yörüngelerdeki elektronları görün.',
    'chemistry.modules.rutherfordModel.cta': 'Modeli aç',
    'chemistry.modules.rutherfordModel.badge.ib': 'IB',
    'chemistry.modules.rutherfordModel.badge.structure': 'Yapı 1',
    'chemistry.modules.more.title': 'Daha fazla kimya modülü',
    'chemistry.modules.more.description': 'Yakında.',
    'chemistry.modules.more.note':
      'Deneyler, tepkimeler ve bağlanma derslerini buraya ekleyin.',
    'modules.more.title': 'Daha fazla görselleştirme',
    'modules.more.description': 'Yakında.',
    'modules.more.note': 'Ürettikçe yeni görselleştirmeleri buraya ekleyin.',
    'tools.stepConverter.title': 'STEP / IGES Dönüştürücü',
    'tools.stepConverter.subtitle':
      'CAD dosyalarını glTF, GLB veya OBJ formatına dönüştürün.',
    'tools.stepConverter.description':
      'STEP veya IGES dosyalarını yükleyin ve web uyumlu çıktılar alın.',
    'tools.stepConverter.cta': 'Dönüştürücüyü aç',
    'tools.stepConverter.badge': 'Deneysel',
    'tools.stepConverter.panel.title': 'Dosya dönüştür',
    'tools.stepConverter.panel.description':
      'STEP/IGES dosyası yükleyin ve çıktı formatını seçin. Büyük modeller birkaç dakika sürebilir.',
    'tools.stepConverter.form.fileLabel': 'Girdi dosyası',
    'tools.stepConverter.form.fileHint':
      'Kabul edilen: .step, .stp (maks 15 MB)',
    'tools.stepConverter.form.filePlaceholder': 'Dosya seç',
    'tools.stepConverter.form.modeLabel': 'Dönüşüm modu',
    'tools.stepConverter.form.modeBasic': 'Temel',
    'tools.stepConverter.form.modeAdvanced': 'Gelişmiş',
    'tools.stepConverter.form.formatLabel': 'Çıktı formatı',
    'tools.stepConverter.form.outputLabel': 'Çıktı',
    'tools.stepConverter.form.outputBundle':
      'ZIP paket (.glb + .metadata.json)',
    'tools.stepConverter.form.linDeflection': 'Lineer sapma',
    'tools.stepConverter.form.angDeflection': 'Açı sapması',
    'tools.stepConverter.form.relative': 'Göreceli sapma',
    'tools.stepConverter.form.parallel': 'Paralel üçgenleme',
    'tools.stepConverter.form.includeBom': 'BOM çıktısını ekle',
    'tools.stepConverter.form.includeNodeMap': 'Düğüm haritasını ekle',
    'tools.stepConverter.form.submit': 'Dönüştür',
    'tools.stepConverter.form.reset': 'Temizle',
    'tools.stepConverter.form.cancel': 'İptal',
    'tools.stepConverter.status.idle': 'Dönüştürmeye hazır.',
    'tools.stepConverter.status.loading': 'Dönüştürülüyor...',
    'tools.stepConverter.status.stage.parsing': 'STEP okunuyor...',
    'tools.stepConverter.status.stage.meshing': 'Mesh oluşturuluyor...',
    'tools.stepConverter.status.stage.writing': 'GLB yazılıyor...',
    'tools.stepConverter.status.stage.metadata': 'Metadata hazırlanıyor...',
    'tools.stepConverter.status.stage.packaging': 'Paket hazırlanıyor...',
    'tools.stepConverter.status.success': 'Dönüştürme tamamlandı.',
    'tools.stepConverter.status.error': 'Dönüştürme başarısız.',
    'tools.stepConverter.status.metadataLoading': 'Metadata hazırlanıyor...',
    'tools.stepConverter.status.metadataSuccess': 'Metadata hazır.',
    'tools.stepConverter.status.metadataError': 'Metadata başarısız.',
    'tools.stepConverter.status.apiUnavailable':
      'Dönüştürücü API ulaşılamıyor. Lütfen tekrar deneyin.',
    'tools.stepConverter.status.timeout':
      'Dönüştürme zaman aşımına uğradı. Lütfen tekrar deneyin.',
    'tools.stepConverter.status.missingFile':
      'Önce bir STEP veya IGES dosyası seçin.',
    'tools.stepConverter.status.invalidNumbers': 'Sapma değerleri sayı olmalı.',
    'tools.stepConverter.error.FILE_TOO_LARGE':
      'Dosya çok büyük. Maksimum boyut 15 MB.',
    'tools.stepConverter.error.UNSUPPORTED_EXTENSION':
      'Desteklenmeyen dosya türü. Lütfen .step veya .stp dosyası seçin.',
    'tools.stepConverter.error.INVALID_STEP':
      'STEP dosyası geçersiz veya bozuk görünüyor. Farklı bir dışa aktarma deneyin.',
    'tools.stepConverter.error.UNSUPPORTED_STEP_CONTENT':
      'Bu STEP dosyasında desteklenen solid/montaj bulunamadı.',
    'tools.stepConverter.error.UNITS_SCALE_MISMATCH':
      'Birim ölçeği hatalı görünüyor (mm vs m). Farklı bir dışa aktarma deneyin.',
    'tools.stepConverter.error.WASM_LOAD_FAILED':
      'Dönüştürme motoru yüklenemedi. Lütfen sayfayı yenileyip tekrar deneyin.',
    'tools.stepConverter.error.OUT_OF_MEMORY':
      'Dönüştürme sırasında bellek tükendi. Daha küçük bir model deneyin.',
    'tools.stepConverter.error.CONVERSION_FAILED':
      'Dönüştürme başarısız. Lütfen tekrar deneyin.',
    'tools.stepConverter.error.METADATA_FAILED':
      'Bu dosya için metadata üretimi başarısız oldu.',
    'tools.stepConverter.error.GLB_PATCH_FAILED':
      'Metadata, GLB çıktısına gömülemedi.',
    'tools.stepConverter.error.ZIP_FAILED':
      'Çıktılar zip pakete dönüştürülemedi.',
    'tools.stepConverter.output.label': 'İndirme',
    'tools.stepConverter.output.cta': 'Paketi indir',
    'tools.stepConverter.output.metadataLabel': 'Metadata çıktıları',
    'tools.stepConverter.output.bomCta': 'BOM JSON indir',
    'tools.stepConverter.output.nodeMapCta': 'Düğüm haritası JSON indir',
    'tools.stepConverterBrowser.title': 'STEP / IGES Dönüştürücü',
    'tools.stepConverterBrowser.subtitle':
      'OpenCascade ile CAD dosyalarını glTF, GLB veya OBJ formatına dönüştürün.',
    'tools.stepConverterBrowser.description':
      'STEP veya IGES dosyalarını yükleyip çıktıları indirin.',
    'tools.stepConverterBrowser.cta': 'Dönüştürücüyü aç',
    'tools.stepConverterBrowser.badge': 'Deneysel',
    'bohrModel.title': 'Bohr Atom Modeli',
    'bohrModel.subtitle':
      'Bohr modelini kullanarak elektron katmanlarını görselleştirin.',
    'bohrModel.card.title': 'Keşif',
    'bohrModel.card.description':
      'Görselleştirmeyi anında güncellemek için bir element seçin.',
    'daltonModel.title': 'Dalton Atom Modeli',
    'daltonModel.subtitle': "Dalton'un katı küre atom modelini keşfedin.",
    'daltonModel.card.title': 'Keşif',
    'daltonModel.card.description':
      'Görselleştirmeyi anında güncellemek için bir element seçin.',
    'thomsonModel.title': 'Thomson Atom Modeli',
    'thomsonModel.subtitle': 'Pozitif yüklü küre içinde elektronları görün.',
    'thomsonModel.card.title': 'Keşif',
    'thomsonModel.card.description':
      'Görselleştirmeyi anında güncellemek için bir element seçin.',
    'rutherfordModel.title': 'Rutherford Atom Modeli',
    'rutherfordModel.subtitle':
      'Yoğun bir merkezin etrafında elektronların yörüngelerini keşfedin.',
    'rutherfordModel.card.title': 'Keşif',
    'rutherfordModel.card.description':
      'Görselleştirmeyi anında güncellemek için bir element seçin.',
    'about.title': 'Bilim Kaşifi Hakkında',
    'about.paragraph1':
      'Bilim Kaşifi, gerçek zamanlı grafiklerle anlaşılır ders içeriğini birleştiren portfolyo odaklı bir alan. STEM konuları için etkileşimli hikaye anlatımı, React mimarisi ve düşünceli bir UX yaklaşımını sergiler.',
    'about.paragraph2':
      'Vite, React, Zustand ve shadcn/ui bileşenleri ile inşa edildi; proje temiz, birleştirilebilir yapılar, durum senkronizasyonu ve three.js destekli görselleri vurgular.',
    'legend.proton': 'Proton',
    'legend.neutron': 'Nötron',
    'legend.electron': 'Elektron',
    'legend.positiveSphere': 'Pozitif küre',
    'element.label': 'Element',
    'stats.atomicNumber': 'Atom numarası',
    'stats.atomicMass': 'Atom kütlesi',
    'stats.protons': 'Proton',
    'stats.neutrons': 'Nötron',
    'stats.electrons': 'Elektron',
    'stats.category': 'Kategori',
    'stats.shells': 'Elektron katmanları',
    'controls.autoRotate': 'Kamerayı otomatik döndür',
    'controls.freezeMotion': 'Hareketi dondur',
    'controls.rotateAtom': 'Atomu döndür',
    'controls.tiltedOrbits': 'Elektron yörüngelerini eğ',
    'controls.showPositiveSphere': 'Pozitif küreyi göster',
    'controls.cutawaySphere': 'Küreyi kesitte göster',
    'controls.showTrails': 'Elektron izlerini göster',
    'controls.explode': 'Patlatılmış görünüm',
    'controls.partsDetected': 'Tespit edilen parçalar',
    'controls.explodeHintSingle': 'Patlatma için birden fazla parça gerekir.',
    'controls.modelHierarchyTitle': 'Model hiyerarşisi',
    'controls.modelHierarchyDescription': 'GLB içindeki düğümleri listeler.',
    'controls.modelHierarchyEmpty': 'Henüz hiyerarşi yok.',
    'controls.partGroupsTitle': 'Benzersiz parçalar',
    'controls.partGroupsDescription': 'Normalize edilmiş parça adlarına göre.',
    'controls.partGroupsEmpty': 'Benzersiz parça bulunamadı.',
    'controls.partGroupsTopAssembly': 'En üst montaj:',
    'controls.assemblyGroupsTitle': 'Alt montajlar',
    'controls.assemblyGroupsDescription': 'Parça içeren adlandırılmış gruplar.',
    'controls.assemblyGroupsEmpty': 'Alt montaj bulunamadı.',
    'controls.debugMaterials': 'Malzeme hata ayıklama',
    'controls.pcfOverlay': 'Karbon ayak izi kaplaması',
    'controls.pcfOverlayMode': 'Kaplama modu',
    'controls.pcfOverlayNone': 'Yok',
    'controls.pcfOverlayTotal': 'Toplam ayak izi',
    'controls.pcfOverlayMaterial': 'Malzeme',
    'controls.pcfOverlayManufacturing': 'Üretim',
    'controls.pcfOverlayTransport': 'Taşıma',
    'controls.pcfLegendLow': 'Düşük',
    'controls.pcfLegendHigh': 'Yüksek',
    'controls.pcfLegendUnit': 'kg CO2e',
    'controls.pcfLegendMaterial': 'Malzeme',
    'controls.pcfLegendManufacturing': 'Üretim',
    'controls.pcfLegendTransport': 'Taşıma',
    'controls.viewTitle': 'Görünüm kontrolleri',
    'controls.orbitPan': 'Kamera kaydırmayı etkinleştir',
    'controls.lockVerticalTilt': 'Dikey eğimi kilitle',
    'controls.resetView': 'Görünümü sıfırla',
    'controls.enterTheater': 'Tiyatro moduna geç',
    'controls.exitTheater': 'Tiyatro modundan çık',
    'controls.showControls': 'Kontrolleri göster',
    'controls.hideControls': 'Kontrolleri gizle',
    'climateTech.tooltip.materialLabel': 'Malzeme',
    'climateTech.tooltip.categoryLabel': 'Kategori',
    'climateTech.tooltip.massLabel': 'Kütle',
    'climateTech.tooltip.partNumberLabel': 'Parça numarası',
    'climateTech.tooltip.sourcingSection': 'Tedarik',
    'climateTech.tooltip.sourcingLabel': 'Tedarik',
    'climateTech.tooltip.sourcingManufactured': 'İç üretim',
    'climateTech.tooltip.sourcingSupplier': 'Tedarikçi',
    'climateTech.tooltip.supplierLabel': 'Tedarikçi',
    'climateTech.tooltip.plantLabel': 'Üretim tesisi',
    'climateTech.tooltip.originLabel': 'Menşei',
    'climateTech.tooltip.materialSection': 'Malzeme',
    'climateTech.tooltip.co2eBreakdown': 'CO2e dökümü',
    'climateTech.tooltip.unknownPart': 'Bilinmeyen parça',
    'climateTech.tooltip.unknownValue': 'Bilinmiyor',
    'units.kg': 'kg',
    'category.Nonmetal': 'Ametal',
    'category.Noble gas': 'Soy gaz',
    'category.Alkali metal': 'Alkali metal',
    'category.Alkaline earth metal': 'Toprak alkali metal',
    'category.Metalloid': 'Yarı metal',
    'category.Halogen': 'Halojen',
    'category.Post-transition metal': 'Geçiş sonrası metal',
    'category.Transition metal': 'Geçiş metali',
    'category.Lanthanide': 'Lantanit',
    'category.Actinide': 'Aktinit',
  },
} as const;

export type SupportedLanguage = keyof typeof TRANSLATIONS;

type TranslationTable = (typeof TRANSLATIONS)['en'];

export type TranslationKey = keyof TranslationTable;

const CATEGORY_KEY_MAP: Record<string, TranslationKey> = {
  Nonmetal: 'category.Nonmetal',
  'Noble gas': 'category.Noble gas',
  'Alkali metal': 'category.Alkali metal',
  'Alkaline earth metal': 'category.Alkaline earth metal',
  Metalloid: 'category.Metalloid',
  Halogen: 'category.Halogen',
  'Post-transition metal': 'category.Post-transition metal',
  'Transition metal': 'category.Transition metal',
  Lanthanide: 'category.Lanthanide',
  Actinide: 'category.Actinide',
};

export function translate(
  language: SupportedLanguage,
  key: TranslationKey
): string {
  const dictionary = TRANSLATIONS[language];
  if (dictionary && key in dictionary) {
    return dictionary[key];
  }

  return TRANSLATIONS.en[key];
}

export function translateCategory(
  language: SupportedLanguage,
  category: string
): string {
  const match = CATEGORY_KEY_MAP[category];
  if (match) {
    return translate(language, match);
  }
  return category;
}
