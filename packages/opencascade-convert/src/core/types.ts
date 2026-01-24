export type OutputFormat = 'obj' | 'gltf' | 'glb';

export type InputFormat = 'step' | 'iges';

export type ReadOptions = {
  preserveNames?: boolean;
  preserveColors?: boolean;
  preserveLayers?: boolean;
  preserveMaterials?: boolean;
};

export type TriangulateOptions = {
  linearDeflection?: number;
  angularDeflection?: number;
  relative?: boolean;
  parallel?: boolean;
};

export type WriteOptions = {
  metadata?: Record<string, string>;
  nameFormat?: NameFormat;
};

export type ConvertOptions = {
  inputPath: string;
  outputPath: string;
  format?: OutputFormat;
  read?: ReadOptions;
  triangulate?: TriangulateOptions;
  write?: WriteOptions;
};

export type ConvertFileOptions = ConvertOptions & {
  loader?: LoaderOptions;
};

export type ConvertBufferOptions = {
  input: Uint8Array;
  inputFormat: InputFormat;
  outputFormat: OutputFormat;
  read?: ReadOptions;
  triangulate?: TriangulateOptions;
  write?: WriteOptions;
};

export type ConvertBufferFileOptions = ConvertBufferOptions & {
  loader?: LoaderOptions;
};

export type BinaryData = Uint8Array;

export type ConvertBufferResult =
  | { outputFormat: 'glb'; glb: BinaryData }
  | { outputFormat: 'gltf'; gltf: BinaryData; bin: BinaryData }
  | { outputFormat: 'obj'; obj: BinaryData };

export type ConvertResult = {
  inputPath: string;
  outputPath: string;
  format: OutputFormat;
};

export type LoaderOptions = {
  cwd?: string;
  cache?: boolean;
};

export type NameFormat =
  | 'empty'
  | 'product'
  | 'instance'
  | 'instanceOrProduct'
  | 'productOrInstance'
  | 'productAndInstance'
  | 'productAndInstanceAndOcaf';

export type AssemblyNodeKind = 'assembly' | 'part';

export type AssemblyNode = {
  id: string;
  labelEntry: string;
  name: string;
  kind: AssemblyNodeKind;
  productId: string;
  productName: string;
  parentId: string | null;
  children: string[];
  path: string[];
};

export type NodeMap = {
  roots: string[];
  nodes: Record<string, AssemblyNode>;
};

export type BomOccurrence = {
  nodeId: string;
  instanceId: string;
  name: string;
  path: string[];
};

export type BomItem = {
  productId: string;
  productName: string;
  kind: AssemblyNodeKind;
  quantity: number;
  instances: BomOccurrence[];
};

export type BomExport = {
  roots: string[];
  items: BomItem[];
};
