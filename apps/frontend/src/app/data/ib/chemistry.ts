export interface IbSyllabusSection {
  id: string;
  label: string;
  title: string;
  topics: Array<{
    id: string;
    label: string;
    title: string;
  }>;
}

export interface IbChemistrySyllabus {
  sections: IbSyllabusSection[];
}

export const IB_CHEMISTRY_SYLLABUS: IbChemistrySyllabus = {
  sections: [
    {
      id: 'structure-1',
      label: 'Structure 1',
      title: 'Models of the particulate nature of matter',
      topics: [
        {
          id: 'structure-1-1',
          label: 'Structure 1.1',
          title: 'Introduction to the particulate nature of matter',
        },
        {
          id: 'structure-1-2',
          label: 'Structure 1.2',
          title: 'The nuclear atom',
        },
        {
          id: 'structure-1-3',
          label: 'Structure 1.3',
          title: 'Electron configurations',
        },
        {
          id: 'structure-1-4',
          label: 'Structure 1.4',
          title: 'Counting particles by mass: The mole',
        },
        {
          id: 'structure-1-5',
          label: 'Structure 1.5',
          title: 'Ideal gases',
        },
      ],
    },
    {
      id: 'structure-2',
      label: 'Structure 2',
      title: 'Models of bonding and structure',
      topics: [
        {
          id: 'structure-2-1',
          label: 'Structure 2.1',
          title: 'The ionic model',
        },
        {
          id: 'structure-2-2',
          label: 'Structure 2.2',
          title: 'The covalent model',
        },
        {
          id: 'structure-2-3',
          label: 'Structure 2.3',
          title: 'The metallic model',
        },
        {
          id: 'structure-2-4',
          label: 'Structure 2.4',
          title: 'From models to materials',
        },
      ],
    },
    {
      id: 'structure-3',
      label: 'Structure 3',
      title: 'Classification of matter',
      topics: [
        {
          id: 'structure-3-1',
          label: 'Structure 3.1',
          title: 'The periodic table: Classification of elements',
        },
        {
          id: 'structure-3-2',
          label: 'Structure 3.2',
          title: 'Functional groups: Classification of organic compounds',
        },
      ],
    },
    {
      id: 'reactivity-1',
      label: 'Reactivity 1',
      title: 'What drives chemical reactions?',
      topics: [
        {
          id: 'reactivity-1-1',
          label: 'Reactivity 1.1',
          title: 'Measuring enthalpy change',
        },
        {
          id: 'reactivity-1-2',
          label: 'Reactivity 1.2',
          title: 'Energy cycles in reactions',
        },
        {
          id: 'reactivity-1-3',
          label: 'Reactivity 1.3',
          title: 'Energy from fuels',
        },
        {
          id: 'reactivity-1-4',
          label: 'Reactivity 1.4',
          title: 'Entropy and spontaneity (Additional higher level)',
        },
      ],
    },
    {
      id: 'reactivity-2',
      label: 'Reactivity 2',
      title: 'How much, how fast and how far?',
      topics: [
        {
          id: 'reactivity-2-1',
          label: 'Reactivity 2.1',
          title: 'How much? The amount of chemical change',
        },
        {
          id: 'reactivity-2-2',
          label: 'Reactivity 2.2',
          title: 'How fast? The rate of chemical change',
        },
        {
          id: 'reactivity-2-3',
          label: 'Reactivity 2.3',
          title: 'How far? The extent of chemical change',
        },
      ],
    },
    {
      id: 'reactivity-3',
      label: 'Reactivity 3',
      title: 'What are the mechanisms of chemical change?',
      topics: [
        {
          id: 'reactivity-3-1',
          label: 'Reactivity 3.1',
          title: 'Proton transfer reactions',
        },
        {
          id: 'reactivity-3-2',
          label: 'Reactivity 3.2',
          title: 'Electron transfer reactions',
        },
        {
          id: 'reactivity-3-3',
          label: 'Reactivity 3.3',
          title: 'Electron sharing reactions',
        },
        {
          id: 'reactivity-3-4',
          label: 'Reactivity 3.4',
          title: 'Electron-pair sharing reactions',
        },
      ],
    },
  ],
};
