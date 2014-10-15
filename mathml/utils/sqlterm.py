from mathml.termbuilder import tree_converters, InfixTermBuilder

__all__ = [ 'SqlTermBuilder' ]

# BUILDER

class SqlTermBuilder(InfixTermBuilder):
    _NAME_MAP = {
        'e'     : 'exp(1.0)',
        'pi'    : 'pi()',
        'true'  : 'TRUE',
        'false' : 'FALSE'
        }

    def _handle_const_bool(self, operator, operands, affin):
        return [ operands[0] and 'TRUE' or 'FALSE' ]

    def _handle_const_complex(self, operator, operands, affin):
        raise NotImplementedError("Complex numbers cannot be converted to SQL.")

    def _handle_interval(self, operator, operands, affin):
        raise NotImplementedError("Intervals cannot be converted to SQL.")


tree_converters.register_converter('sql', SqlTermBuilder())
