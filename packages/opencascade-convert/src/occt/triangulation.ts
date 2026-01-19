import type { TriangulateOptions } from '../core/types';
import type { OpenCascadeInstance } from './types';

export type OcctDocument = any;

const DEFAULT_TRIANGULATE_OPTIONS: Required<TriangulateOptions> = {
  linearDeflection: 0.1,
  angularDeflection: 0.1,
  relative: false,
  parallel: false,
};

export function triangulateDocument(
  oc: OpenCascadeInstance,
  doc: OcctDocument,
  options: TriangulateOptions = {}
) {
  const settings = { ...DEFAULT_TRIANGULATE_OPTIONS, ...options };
  const tool = oc.XCAFDoc_DocumentTool.ShapeTool(doc.Main()).get();
  const builder = new oc.BRep_Builder();
  const compound = new oc.TopoDS_Compound();
  builder.MakeCompound(compound);
  const sequence = new oc.TDF_LabelSequence_1();
  tool.GetFreeShapes(sequence);

  for (let index = sequence.Lower(); index <= sequence.Upper(); index += 1) {
    const label = sequence.Value(index);
    const shape = oc.XCAFDoc_ShapeTool.GetShape_2(label);
    if (shape) {
      builder.Add(compound, shape);
    }
  }

  new oc.BRepMesh_IncrementalMesh_2(
    compound,
    settings.linearDeflection,
    settings.relative,
    settings.angularDeflection,
    settings.parallel
  );
}
