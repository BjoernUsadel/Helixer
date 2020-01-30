"""convert cleaned-db schema to numeric values describing gene structure"""

import numpy as np
import logging
from abc import ABC, abstractmethod
from sqlalchemy.orm.exc import NoResultFound

from geenuff.base import types
from geenuff.base.orm import Coordinate, Genome
from ..core.orm import Mer


AMBIGUITY_DECODE = {
    'C': [1., 0., 0., 0.],
    'A': [0., 1., 0., 0.],
    'T': [0., 0., 1., 0.],
    'G': [0., 0., 0., 1.],
    'Y': [0.5, 0., 0.5, 0.],
    'R': [0., 0.5, 0., 0.5],
    'W': [0., 0.5, 0.5, 0.],
    'S': [0.5, 0., 0., 0.5],
    'K': [0., 0., 0.5, 0.5],
    'M': [0.5, 0.5, 0., 0.],
    'D': [0., 0.33, 0.33, 0.33],
    'V': [0.33, 0.33, 0., 0.33],
    'H': [0.33, 0.33, 0.33, 0.],
    'B': [0.33, 0., 0.33, 0.33],
    'N': [0.25, 0.25, 0.25, 0.25]
}


class Stepper(object):
    def __init__(self, end, by):
        self.at = 0
        self.end = end
        self.by = by

    def step(self):
        prev = self.at
        if prev + self.by < self.end:
            new = prev + self.by
        else:
            new = self.end
        self.at = new
        return prev, new

    def step_to_end(self):
        while self.at < self.end:
            yield self.step()


class Numerifier(ABC):
    def __init__(self, n_cols, coord, max_len, dtype=np.float32):
        assert isinstance(n_cols, int)
        self.n_cols = n_cols
        self.coord = coord
        self.max_len = max_len
        self.dtype = dtype
        self.matrix = None
        self.error_mask = None
        # set paired steps
        partitioner = Stepper(end=self.coord.length, by=self.max_len)
        self.paired_steps = list(partitioner.step_to_end())

        super().__init__()

    @abstractmethod
    def coord_to_matrices(self):
        """Method to be called from outside. Numerifies both strands."""
        pass

    def _slice_matrix(self, matrix, error_mask, is_plus_strand):
        data = []
        error_masks = []
        # reverse steps on minus strand
        steps = self.paired_steps if is_plus_strand else self.paired_steps[::-1]
        for prev, current in steps:
            data_slice = matrix[prev:current]
            error_mask_slice = error_mask[prev:current]
            if not is_plus_strand:
                # invert directions
                data_slice = np.flip(data_slice, axis=0)
                error_mask_slice = np.flip(error_mask_slice, axis=0)
            data.append(data_slice)
            error_masks.append(error_mask_slice)
        return data, error_masks

    def _zero_matrix(self):
        length = len(self.coord.sequence)
        self.matrix = np.zeros((length, self.n_cols,), self.dtype)
        # 0 means error so this can be used directly as sample weight later on
        self.error_mask = np.ones((length,), np.int8)


class AnnotationNumerifier(Numerifier):
    """Class for the numerification of the labels. Outputs a matrix that
    fits the sequence length of the coordinate but only for the provided features.
    This is done to support alternative splicing in the future.
    """
    feature_to_col = {
        types.GeenuffFeature.geenuff_transcript: 0,
        types.GeenuffFeature.geenuff_cds: 1,
        types.GeenuffFeature.geenuff_intron: 2,
     }

    def __init__(self, coord, features, max_len, one_hot=True):
        Numerifier.__init__(self, n_cols=3, coord=coord, max_len=max_len, dtype=np.int8)
        self.features = features
        self.one_hot = one_hot

    def coord_to_matrices(self):
        """Always numerifies both strands one after the other."""
        plus_strand = self._encode_strand(True)
        minus_strand = self._encode_strand(False)

        # put everything together
        labels = plus_strand[0] + minus_strand[0]
        error_masks = plus_strand[1] + minus_strand[1]
        return labels, error_masks

    def _encode_strand(self, bool_):
        self._zero_matrix()
        self._update_matrix_and_error_mask(is_plus_strand=bool_)

        if self.one_hot:
            self.onehot4_matrix = self._encode_onehot4()
            labels, error_masks = self._slice_matrix(self.onehot4_matrix,
                                                     self.error_mask,
                                                     is_plus_strand=bool_)
        else:
            labels, error_masks = self._slice_matrix(self.matrix,
                                                     self.error_mask,
                                                     is_plus_strand=bool_)
        return labels, error_masks

    def _update_matrix_and_error_mask(self, is_plus_strand):
        for feature in self.features:
            # don't include features from the other strand
            if not feature.is_plus_strand == is_plus_strand:
                continue
            start = feature.start
            end = feature.end
            if not is_plus_strand:
                start, end = end + 1, start + 1
            if feature.type in AnnotationNumerifier.feature_to_col.keys():
                col = AnnotationNumerifier.feature_to_col[feature.type]
                self.matrix[start:end, col] = 1
            elif feature.type.value in types.geenuff_error_type_values:
                self.error_mask[start:end] = 0
            else:
                raise ValueError('Unknown feature type found: {}'.format(feature.type.value))

    def _encode_onehot4(self):
        # Class order: Intergenic, UTR, CDS, (non-coding Intron), Intron
        # This could be done in a more efficient way, but this way we may catch bugs
        # where non-standard classes are output in the multiclass output
        one_hot_matrix = np.zeros((self.matrix.shape[0], 4), dtype=bool)
        col_0, col_1, col_2 = self.matrix[:, 0], self.matrix[:, 1], self.matrix[:, 2]
        # Intergenic
        one_hot_matrix[:, 0] = np.logical_not(col_0)
        # UTR
        genic_non_coding = np.logical_and(col_0, np.logical_not(col_1))
        one_hot_matrix[:, 1] = np.logical_and(genic_non_coding, np.logical_not(col_2))
        # CDS
        one_hot_matrix[:, 2] = np.logical_and(np.logical_and(col_0, col_1), np.logical_not(col_2))
        # Introns
        one_hot_matrix[:, 3] = np.logical_and(col_0, col_2)
        assert np.all(np.count_nonzero(one_hot_matrix, axis=1) == 1)

        one_hot4_matrix = one_hot_matrix.astype(np.int8)
        return one_hot4_matrix


class CoordNumerifier(object):
    """Combines the different Numerifiers which need to operate on the same Coordinate
    to ensure consistent parameters. Selects all Features of the given Coordinate.
    """
    @staticmethod
    def numerify(geenuff_exporter, coord, coord_features, max_len, one_hot=True):
        assert isinstance(max_len, int) and max_len > 0
        if not coord_features:
            logging.warning('Sequence {} has no annoations'.format(coord.seqid))

        anno_numerifier = AnnotationNumerifier(coord=coord, features=coord_features, max_len=max_len,
                                               one_hot=one_hot)

        # returns results for both strands, with the plus strand first in the list
        labels, label_masks = anno_numerifier.coord_to_matrices()

        start_ends = anno_numerifier.paired_steps
        # flip the start ends back for - strand and append
        start_ends += [(x[1], x[0]) for x in anno_numerifier.paired_steps[::-1]]

        # do not output the input_masks as it is not used for anything
        out = {
            'labels': labels,
            'label_masks': label_masks,
            'species': [coord.genome.species.encode('ASCII')] * len(labels),
            'seqids': [coord.seqid.encode('ASCII')] * len(labels),
            'start_ends': start_ends,
        }
        return out
