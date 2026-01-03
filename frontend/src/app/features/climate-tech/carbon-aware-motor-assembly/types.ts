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
  key: string;
  name: string;
  material_guess?: string;
};

export type HierarchyItem = {
  name: string;
  depth: number;
  type: string;
};
