export type AssemblyGroup = {
  name: string;
  path: string;
  meshCount: number;
};

export type PartGroup = {
  key: string;
  name: string;
  count: number;
  assemblies: { name: string; count: number }[];
};

export type PartMaterialMeta = {
  id?: string;
  key: string;
  name: string;
  material_guess?: string;
  pcf?: {
    kgco2e_est?: number;
    breakdown?: {
      material?: number;
      manufacturing?: number;
      transport?: number;
    };
  };
};

export type PcfOverlayMode = 'total' | 'material' | 'manufacturing' | 'transport';

export type HierarchyItem = {
  name: string;
  depth: number;
  type: string;
};
