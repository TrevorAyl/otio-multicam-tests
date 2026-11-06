"""Experimental OTIO SchemaDef classes, NOT upstream OTIO core schemas.

Install using the accompanying OTIO_PLUGIN_MANIFEST_PATH manifest.
"""
import opentimelineio as otio


@otio.core.register_type
class MulticamPackage(otio.core.SerializableObject):
    _serializable_label = 'MulticamPackage.1'
    timeline = otio.core.serializable_field('timeline')
    definitions = otio.core.serializable_field('definitions')
    composition_references = otio.core.serializable_field('composition_references')
    operations = otio.core.serializable_field('operations')
    version = otio.core.serializable_field('version')
    media = otio.core.serializable_field('media')
    selectors = otio.core.serializable_field('selectors')
    angle_definitions = otio.core.serializable_field('angle_definitions')
    output_references = otio.core.serializable_field('output_references')
    composite_outputs = otio.core.serializable_field('composite_outputs')

    def __init__(self, timeline=None, definitions=None, composition_references=None, operations=None, media=None, selectors=None, angle_definitions=None, output_references=None, composite_outputs=None):
        super().__init__()
        self.timeline = timeline
        self.definitions = list(definitions or [])
        self.composition_references = list(composition_references or [])
        self.operations = list(operations or [])
        self.media = list(media or [])
        self.selectors = list(selectors or [])
        self.angle_definitions = list(angle_definitions or [])
        self.output_references = list(output_references or [])
        self.composite_outputs = list(composite_outputs or [])
        self.version = '0.6-experimental'


@otio.core.register_type
class CompositionDefinition(otio.core.SerializableObject):
    _serializable_label = 'CompositionDefinition.1'
    definition_id = otio.core.serializable_field('definition_id')
    name = otio.core.serializable_field('name')
    kind = otio.core.serializable_field('kind')
    rate = otio.core.serializable_field('rate')
    angles = otio.core.serializable_field('angles')
    layers = otio.core.serializable_field('layers')
    attributes = otio.core.serializable_field('attributes')

    def __init__(self, definition_id='', name='', kind='composition', rate=25, angles=None, layers=None, attributes=None):
        super().__init__()
        self.definition_id = definition_id
        self.name = name
        self.kind = kind  # 'multicam' | 'composite' | 'sequence'
        self.rate = rate
        self.angles = list(angles or [])  # dicts {angle_id, reference_id}; stable order
        self.layers = list(layers or [])  # dicts {reference_id, operation_id?, order}
        self.attributes = dict(attributes or {})


@otio.core.register_type
class CompositionReference(otio.core.SerializableObject):
    _serializable_label = 'CompositionReference.1'
    occurrence_id = otio.core.serializable_field('occurrence_id')
    definition_id = otio.core.serializable_field('definition_id')
    timing = otio.core.serializable_field('timing')
    selections = otio.core.serializable_field('selections')
    nested_selections = otio.core.serializable_field('nested_selections')
    attributes = otio.core.serializable_field('attributes')

    def __init__(self, occurrence_id='', definition_id='', timing=None, selections=None, attributes=None, nested_selections=None):
        super().__init__()
        self.occurrence_id = occurrence_id
        self.definition_id = definition_id
        self.timing = dict(timing or {})
        self.selections = dict(selections or {})  # {video: angle_id, audio: angle_id}
        self.nested_selections = dict(nested_selections or {})  # local paths, e.g. quad-in-outer/box-0 -> {video:B02}
        self.attributes = dict(attributes or {})


@otio.core.register_type
class CompositeOperation(otio.core.SerializableObject):
    _serializable_label = 'CompositeOperation.1'
    operation_id = otio.core.serializable_field('operation_id')
    operation_type = otio.core.serializable_field('operation_type')
    inputs = otio.core.serializable_field('inputs')
    parameters = otio.core.serializable_field('parameters')

    def __init__(self, operation_id='', operation_type='', inputs=None, parameters=None):
        super().__init__()
        self.operation_id = operation_id
        self.operation_type = operation_type
        self.inputs = dict(inputs or {})  # {fill: reference_id, matte: reference_id}
        self.parameters = dict(parameters or {})


@otio.core.register_type
class RelinkableMedia(otio.core.SerializableObject):
    _serializable_label = 'RelinkableMedia.1'
    media_id = otio.core.serializable_field('media_id')
    display_name = otio.core.serializable_field('display_name')
    identity = otio.core.serializable_field('identity')
    tracks = otio.core.serializable_field('tracks')
    provenance = otio.core.serializable_field('provenance')

    def __init__(self, media_id='', display_name='', identity=None, tracks=None, provenance=None):
        super().__init__()
        self.media_id = media_id
        self.display_name = display_name
        self.identity = dict(identity or {})
        self.tracks = list(tracks or [])
        self.provenance = dict(provenance or {})


@otio.core.register_type
class MulticamSelector(otio.core.SerializableObject):
    """One fixed selection over an edit segment; alternatives are references to source outputs."""
    _serializable_label = 'MulticamSelector.1'
    selector_id = otio.core.serializable_field('selector_id')
    occurrence_id = otio.core.serializable_field('occurrence_id')
    stream = otio.core.serializable_field('stream')
    selected = otio.core.serializable_field('selected')
    alternatives = otio.core.serializable_field('alternatives')
    timing = otio.core.serializable_field('timing')
    provenance = otio.core.serializable_field('provenance')
    portable_selection = otio.core.serializable_field('portable_selection')

    def __init__(self, selector_id='', occurrence_id='', stream='unknown', selected=None, alternatives=None, timing=None, provenance=None, portable_selection=None):
        super().__init__()
        self.portable_selection = dict(portable_selection or {})
        self.selector_id = selector_id
        self.occurrence_id = occurrence_id
        self.stream = stream
        self.selected = dict(selected or {})
        self.alternatives = list(alternatives or [])
        self.timing = dict(timing or {})
        self.provenance = dict(provenance or {})


@otio.core.register_type
class AngleDefinition(otio.core.SerializableObject):
    """Numeric stable ID scoped to one source definition AND selectable stream/group."""
    _serializable_label = 'AngleDefinition.1'
    angle_id = otio.core.serializable_field('angle_id')
    definition_id = otio.core.serializable_field('definition_id')
    group_id = otio.core.serializable_field('group_id')
    display_order = otio.core.serializable_field('display_order')
    output_ref_id = otio.core.serializable_field('output_ref_id')
    label = otio.core.serializable_field('label')
    provenance = otio.core.serializable_field('provenance')

    def __init__(self, angle_id=1, definition_id='', group_id='', display_order=1, output_ref_id='', label='', provenance=None):
        super().__init__()
        self.angle_id = int(angle_id)
        self.definition_id = definition_id
        self.group_id = group_id
        self.display_order = int(display_order)
        self.output_ref_id = output_ref_id
        self.label = label
        self.provenance = dict(provenance or {})


@otio.core.register_type
class OutputReference(otio.core.SerializableObject):
    """Typed output of media, composition or operation; not the occurrence using it."""
    _serializable_label = 'OutputReference.1'
    output_ref_id = otio.core.serializable_field('output_ref_id')
    definition_id = otio.core.serializable_field('definition_id')
    output_type = otio.core.serializable_field('output_type')
    source = otio.core.serializable_field('source')
    provenance = otio.core.serializable_field('provenance')

    def __init__(self, output_ref_id='', definition_id='', output_type='unknown', source=None, provenance=None):
        super().__init__()
        self.output_ref_id = output_ref_id
        self.definition_id = definition_id
        self.output_type = output_type
        self.source = dict(source or {})
        self.provenance = dict(provenance or {})


@otio.core.register_type
class CompositeOutput(otio.core.SerializableObject):
    """A named output port of a reusable composition or compositing operation."""
    _serializable_label = 'CompositeOutput.1'
    output_id = otio.core.serializable_field('output_id')
    owner_definition_id = otio.core.serializable_field('owner_definition_id')
    stream_kind = otio.core.serializable_field('stream_kind')
    operation_id = otio.core.serializable_field('operation_id')
    channels = otio.core.serializable_field('channels')
    alpha_mode = otio.core.serializable_field('alpha_mode')
    attributes = otio.core.serializable_field('attributes')

    def __init__(self, output_id='', owner_definition_id='', stream_kind='picture',
                 operation_id='', channels=None, alpha_mode='none', attributes=None):
        super().__init__()
        self.output_id = output_id
        self.owner_definition_id = owner_definition_id
        self.stream_kind = stream_kind
        self.operation_id = operation_id
        self.channels = list(channels or [])
        self.alpha_mode = alpha_mode
        self.attributes = dict(attributes or {})
