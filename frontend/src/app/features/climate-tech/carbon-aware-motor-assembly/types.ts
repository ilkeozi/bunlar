import type { Mesh } from 'three';

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
  label?: string;
  material?: string;
  category?: string;
  material_guess?: string;
  part_number?: string;
  supplier_name?: string;
  plant_name?: string;
  country_of_origin?: string;
  sourcing?: 'manufactured' | 'supplier';
  pcf?: {
    kgco2e_est?: number;
    mass_kg_est?: number;
    breakdown?: {
      material?: number;
      manufacturing?: number;
      transport?: number;
    };
  };
};

export type SelectedPart = {
  mesh: Mesh;
  meta?: PartMaterialMeta;
};

export type PcfOverlayMode =
  | 'none'
  | 'total'
  | 'material'
  | 'manufacturing'
  | 'transport';

export type HierarchyItem = {
  name: string;
  depth: number;
  type: string;
};
