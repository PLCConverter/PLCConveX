from lark import Lark, Transformer, Visitor, Tree, Token
from lark.visitors import v_args # For decorating visitor methods

# Assume st_grammar_string contains the full Lark grammar for ST
# For production, load from a.lark file
# with open("st_grammar.lark", "r") as f:
#     st_grammar_string = f.read()

# Example: Using a placeholder string for the grammar
st_grammar_string = """
    start: (pou_declaration | var_block | type_definition_block)+
declaration_sections : var_block_list? type_definition_block?
    // --- POU Declarations ---
    pou_declaration : program_declaration | function_block_declaration | function_declaration
program_declaration : PROGRAM_KW IDENTIFIER declaration_sections statement_list END_PROGRAM_KW
function_block_declaration : FUNCTION_BLOCK_KW IDENTIFIER declaration_sections statement_list END_FUNCTION_BLOCK_KW
function_declaration : FUNCTION_KW IDENTIFIER COLON type_specifier declaration_sections statement_list END_FUNCTION_KW

    // --- Variable Declarations ---
    var_block_list : var_block+
    var_block : var_qualifier_block var_decl_item_list END_VAR_KW
    var_qualifier_block : VAR_KW | VAR_INPUT_KW | VAR_OUTPUT_KW | VAR_IN_OUT_KW | VAR_GLOBAL_KW | VAR_TEMP_KW
    var_decl_item_list : var_decl_item (SEMICOLON var_decl_item)* SEMICOLON?
    var_decl_item : identifier_list COLON type_specifier
    identifier_list : IDENTIFIER (COMMA IDENTIFIER)*
    initial_value_expression : expression

    // --- Type Specifiers ---
    type_specifier : elementary_type_name | array_type_spec | struct_type_spec | IDENTIFIER
    elementary_type_name : BOOL_KW | SINT_KW | INT_KW | DINT_KW | LINT_KW | USINT_KW | UINT_KW | UDINT_KW | ULINT_KW
| REAL_KW | LREAL_KW | TIME_KW | DATE_KW | TOD_KW | DT_KW
| STRING_KW
| WSTRING_KW
| BYTE_KW | WORD_KW | DWORD_KW | LWORD_KW
    array_type_spec : ARRAY_KW LBRACKET array_subscripts RBRACKET OF_KW type_specifier
    array_subscripts : array_subscript_range (COMMA array_subscript_range)*
    array_subscript_range : expression ".." expression
    struct_type_spec : STRUCT_KW struct_element_decl_list END_STRUCT_KW
    struct_element_decl_list : struct_element_decl (SEMICOLON struct_element_decl)* SEMICOLON?
    struct_element_decl : IDENTIFIER COLON type_specifier

    // --- User-Defined Type Declarations ---
    type_definition_block : TYPE_KW type_declaration_list END_TYPE_KW
    type_declaration_list : type_declaration (SEMICOLON type_declaration)* SEMICOLON?
    type_declaration : IDENTIFIER COLON type_specifier

    // --- Statements ---
    statement_list :
               | statement (SEMICOLON statement)* SEMICOLON? 
    statement : assignment_statement | if_statement | case_statement | for_statement | while_statement | repeat_statement | function_block_invocation | return_statement | exit_statement | null_statement
    assignment_statement : variable_access ASSIGN expression
    if_statement : IF_KW expression THEN_KW statement_list (ELSIF_KW expression THEN_KW statement_list)* END_IF_KW 
    case_statement : CASE_KW expression OF_KW case_element* END_CASE_KW 
    case_element : case_list COLON statement_list
    case_list : case_value (COMMA case_value)*
    case_value : literal | IDENTIFIER | literal ".." literal
    for_statement : FOR_KW IDENTIFIER ASSIGN expression TO_KW expression? DO_KW statement_list END_FOR_KW
    while_statement : WHILE_KW expression DO_KW statement_list END_WHILE_KW
    repeat_statement : REPEAT_KW statement_list UNTIL_KW expression END_REPEAT_KW
    exit_statement : EXIT_KW
    return_statement : RETURN_KW
    null_statement : SEMICOLON
    function_block_invocation : IDENTIFIER LPAREN [param_assignment_list] RPAREN

    // --- Expressions ---
    expression : or_expression
    or_expression : xor_expression (OR_OP xor_expression)*
    xor_expression : and_expression (XOR_OP and_expression)*
    and_expression : comparison_expression (AND_OP comparison_expression)* // Renamed to avoid conflict with 'comparison' terminal name if any
    comparison_expression : equality_expression ( (EQ | NE) equality_expression )* // Renamed
    equality_expression : relational_expression ( (LT | GT | LE | GE) relational_expression )* // Renamed
    relational_expression : add_expression // Placeholder, was equ_expression
    add_expression : term ( (ADD | SUB) term )*
    term : power_expression ( (MUL | DIV | MOD_OP) power_expression )*
    power_expression : unary_expression (POWER unary_expression)*
    unary_expression : (SUB | NOT_OP)? primary_expression
    primary_expression : literal | variable_access | function_call | LPAREN expression RPAREN

    literal : typed_literal | untyped_literal
    typed_literal : (SINT_KW | INT_KW | DINT_KW | LINT_KW | USINT_KW | UINT_KW | UDINT_KW | ULINT_KW) HASH SIGNED_NUMBER -> typed_integer_literal
| (REAL_KW | LREAL_KW) HASH SIGNED_NUMBER -> typed_real_literal
| (TIME_KW) HASH TIME_VALUE -> typed_time_literal
| (DATE_KW) HASH DATE_VALUE -> typed_date_literal
| (TOD_KW) HASH TOD_VALUE -> typed_tod_literal
| (DT_KW) HASH DT_VALUE -> typed_dt_literal
| (BYTE_KW | WORD_KW | DWORD_KW | LWORD_KW) HASH (HEX_INTEGER | BIN_INTEGER | OCT_INTEGER | SIGNED_NUMBER) -> typed_bitstring_literal

    untyped_literal : SIGNED_NUMBER -> integer_or_real_literal // Context will differentiate INT/REAL or default to one
| BOOLEAN_LITERAL
| STRING_LITERAL
| TIME_VALUE -> time_literal
| DATE_VALUE -> date_literal
| TOD_VALUE -> tod_literal
| DT_VALUE -> dt_literal
| HEX_INTEGER -> hex_literal
| BIN_INTEGER -> bin_literal
| OCT_INTEGER -> oct_literal


    variable_access : IDENTIFIER (array_accessor | struct_member_accessor)*
    array_accessor : LBRACKET expression_list RBRACKET
    struct_member_accessor : DOT IDENTIFIER
    expression_list : expression (COMMA expression)*

    function_call : IDENTIFIER LPAREN [param_assignment_list] RPAREN
    param_assignment_list : param_assignment (COMMA param_assignment)*
    param_assignment : (IDENTIFIER ASSIGN)? expression 

    // --- Terminals ---
    PROGRAM_KW: "PROGRAM"i | "PROGRAMME"i
    END_PROGRAM_KW: "END_PROGRAM"i | "END_PROGRAMME"i
    FUNCTION_BLOCK_KW: "FUNCTION_BLOCK"i
    END_FUNCTION_BLOCK_KW: "END_FUNCTION_BLOCK"i
    FUNCTION_KW: "FUNCTION"i
    END_FUNCTION_KW: "END_FUNCTION"i
    VAR_KW: "VAR"i
    VAR_INPUT_KW: "VAR_INPUT"i
    VAR_OUTPUT_KW: "VAR_OUTPUT"i
    VAR_IN_OUT_KW: "VAR_IN_OUT"i
    VAR_GLOBAL_KW: "VAR_GLOBAL"i
    VAR_TEMP_KW: "VAR_TEMP"i
    END_VAR_KW: "END_VAR"i
    TYPE_KW: "TYPE"i
    END_TYPE_KW: "END_TYPE"i
    STRUCT_KW: "STRUCT"i
    END_STRUCT_KW: "END_STRUCT"i
    ARRAY_KW: "ARRAY"i
    OF_KW: "OF"i

    BOOL_KW: "BOOL"i
    SINT_KW: "SINT"i
    INT_KW: "INT"i
    DINT_KW: "DINT"i
    LINT_KW: "LINT"i
    USINT_KW: "USINT"i
    UINT_KW: "UINT"i
    UDINT_KW: "UDINT"i
    ULINT_KW: "ULINT"i
    REAL_KW: "REAL"i
    LREAL_KW: "LREAL"i
    TIME_KW: "TIME"i
    DATE_KW: "DATE"i
    TOD_KW: "TOD"i | "TIME_OF_DAY"i
    DT_KW: "DT"i | "DATE_AND_TIME"i
    STRING_KW: "STRING"i
    WSTRING_KW: "WSTRING"i
    BYTE_KW: "BYTE"i
    WORD_KW: "WORD"i
    DWORD_KW: "DWORD"i
    LWORD_KW: "LWORD"i

    IF_KW: "IF"i
    THEN_KW: "THEN"i
    ELSE_KW: "ELSE"i
    ELSIF_KW: "ELSIF"i
    END_IF_KW: "END_IF"i
    CASE_KW: "CASE"i
    // OF_KW already defined
    END_CASE_KW: "END_CASE"i
    FOR_KW: "FOR"i
    TO_KW: "TO"i
    BY_KW: "BY"i
    DO_KW: "DO"i
    END_FOR_KW: "END_FOR"i
    WHILE_KW: "WHILE"i
    END_WHILE_KW: "END_WHILE"i
    REPEAT_KW: "REPEAT"i
    UNTIL_KW: "UNTIL"i
    END_REPEAT_KW: "END_REPEAT_KW"i
    EXIT_KW: "EXIT"i
    RETURN_KW: "RETURN"i

    TRUE_KW: "TRUE"i
    FALSE_KW: "FALSE"i
    BOOLEAN_LITERAL: TRUE_KW | FALSE_KW

    OR_OP: "OR"i
    XOR_OP: "XOR"i
    AND_OP: "AND"i | "&"
    NOT_OP: "NOT"i
    MOD_OP: "MOD"i

    ASSIGN: ":="
    ADD: "+"
    SUB: "-"
    MUL: "*"
    DIV: "/"
    POWER: "**"
    EQ: "="
    NE: "<>"
    LT: "<"
    GT: ">"
    LE: "<="
    GE: ">="

    LPAREN: "("
    RPAREN: ")"
    LBRACKET: "["
    RBRACKET: "]"
    DOT: "."
    COMMA: ","
    SEMICOLON: ";"
    COLON: ":"
    HASH: "#"
    DOUBLE_DOT: ".." // For ranges like 1..10

    %import common.SIGNED_NUMBER
    %import common.ESCAPED_STRING -> STRING_LITERAL // Using alias for clarity
    %import common.WS
    %ignore WS

    IDENTIFIER: /[a-zA-Z_][a-zA-Z0-9_]*/
    INTEGER_LITERAL: SIGNED_NUMBER // Lark's SIGNED_NUMBER can be int

TIME_VALUE: /(?:(?:[0-9]+)(?:[0-9]+[hH_])?(?:[0-9]+[mM_])?(?:[0-9]+)?(?:[0-9]+?)?|(?:[0-9]+[hH_])(?:[0-9]+[mM_])?(?:[0-9]+)?(?:[0-9]+?)?|(?:[0-9]+[mM_])(?:[0-9]+)?(?:[0-9]+?)?|(?:[0-9]+)(?:[0-9]+?)?|(?:[0-9]+?))/
    DATE_VALUE: /[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}/
    TOD_VALUE:  /[0-9]{1,2}:[0-9]{1,2}(:[0-9]{1,2}(\.[0-9]+)?)?/
    DT_VALUE:   DATE_VALUE "-" TOD_VALUE

    HEX_INTEGER: /16#[0-9a-fA-F_]+/i
    OCT_INTEGER: /8#[0-7_]+/i
    BIN_INTEGER: /2#[01_]+/i


    COMMENT_SL: "//" /.*/
    COMMENT_ML: "(*" /.*?/s "*)"
    %ignore COMMENT_SL
    %ignore COMMENT_ML
"""

st_parser = Lark(st_grammar_string, start='start', parser='lalr', lexer='contextual', keep_all_tokens=False)



class Symbol:
    def __init__(self, name, type_obj, kind, location=None): # kind: 'variable', 'type', 'function', 'fb', 'program'
        self.name = name
        self.type = type_obj # This could be a string or a custom Type object
        self.kind = kind
        self.location = location # Optional: AST node of declaration

    def __repr__(self):
        return f"Symbol(name='{self.name}', type='{self.type}', kind='{self.kind}')"

class Scope:
    def __init__(self, parent=None, name="<scope>"):
        self.parent = parent
        self.name = name
        self.symbols = {} # name: Symbol

    def add_symbol(self, symbol):
        if symbol.name in self.symbols:
            # Simple overwrite, or could raise an error for re-declaration
            pass
        self.symbols[symbol.name] = symbol

    def lookup_symbol(self, name):
        symbol = self.symbols.get(name)
        if symbol:
            return symbol
        if self.parent:
            return self.parent.lookup_symbol(name)
        return None

    def __repr__(self):
        return f"Scope(name='{self.name}', symbols={list(self.symbols.keys())})"

class SymbolTable:
    def __init__(self):
        self.global_scope = Scope(name="<global>")
        self.current_scope = self.global_scope
        # Predefined types
        for t_name in ["BOOL", "SINT", "INT", "DINT", "LINT", "USINT", "UINT", "UDINT", "ULINT", "REAL", "LREAL", "TIME", "DATE", "TOD", "DT", "STRING", "WSTRING", "BYTE", "WORD", "DWORD", "LWORD"]:
            self.global_scope.add_symbol(Symbol(t_name, t_name, 'predefined_type'))


    def enter_scope(self, name="<anonymous_scope>"):
        new_scope = Scope(parent=self.current_scope, name=name)
        self.current_scope = new_scope
        return new_scope

    def exit_scope(self):
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
        else:
            # Cannot exit global scope, or handle as error
            pass
        
class StDataType: # Base class for structured type information
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return self.name
    def __eq__(self, other):
        if isinstance(other, StDataType):
            return self.name == other.name
        if isinstance(other, str): # Allow comparison with string representation
            return self.name == other.upper() # Assuming type names are stored uppercase
        return False
    def __hash__(self): # Required if StDataType objects are used as dict keys
        return hash(self.name)

class ElementaryType(StDataType): pass
class ArrayType(StDataType):
    def __init__(self, element_type, dimensions): # dimensions: list of (low, high) tuples
        super().__init__(f"ARRAY {dimensions} OF {element_type}")
        self.element_type = element_type
        self.dimensions = dimensions
class StructType(StDataType):
    def __init__(self, name, fields): # fields: dict of {field_name: field_type_obj}
        super().__init__(name if name else "ANON_STRUCT")
        self.fields = fields # {name: StDataType_object}
class PouType(StDataType): # For FBs/Functions used as types or for their signature
    def __init__(self, name, pou_kind, return_type=None, params=None): # params: list of Symbol
        super().__init__(name)
        self.pou_kind = pou_kind # "FUNCTION", "FUNCTION_BLOCK", "PROGRAM"
        self.return_type = return_type # StDataType_object or None
        self.params = params if params else "fuck"


class SymbolTableBuilder(Visitor):
    def __init__(self, symbol_table):
        self.st = symbol_table

    def _resolve_type_specifier(self, ts_node):
        if not isinstance(ts_node, Tree): # Should be a Tree
            return ElementaryType("UNKNOWN_TYPE_SPEC")

        if ts_node.data == "elementary_type_name":
            # Child is a Token like INT_KW, REAL_KW
            type_name_token = ts_node.children
            type_name_str = type_name_token.type.replace("_KW", "") # e.g. INT_KW -> INT
            # Handle STRING[size] if needed
            if type_name_str in ("STRING", "WSTRING") and len(ts_node.children) > 1:
                 # Simplified: just capture base type for now
                return ElementaryType(type_name_str)
            return ElementaryType(type_name_str)
        elif ts_node.data == "identifier": # User-defined type
            type_name = ts_node.children.value
            sym = self.st.current_scope.lookup_symbol(type_name)
            return sym.type if sym and sym.kind == 'type' else ElementaryType(type_name) # Return the StDataType object
        elif ts_node.data == "array_type_spec":
            # ARRAY_KW LBRACKET array_subscripts RBRACKET OF_KW type_specifier
            # For simplicity, dimensions are not fully resolved here, just structure
            element_type_node = ts_node.children[-1] # Last child is type_specifier
            element_type = self._resolve_type_specifier(element_type_node)
            # Dimensions would need evaluation of expressions in array_subscripts
            return ArrayType(element_type, "dims_placeholder")
        elif ts_node.data == "struct_type_spec":
            # STRUCT_KW struct_element_decl_list END_STRUCT_KW
            fields = {}
            # Temporarily enter a pseudo-scope for struct fields if needed, or handle flatly
            if len(ts_node.children) > 1 and isinstance(ts_node.children, Tree) and ts_node.children.data == "struct_element_decl_list":
                for struct_elem_decl in ts_node.children.children:
                    if isinstance(struct_elem_decl, Tree) and struct_elem_decl.data == "struct_element_decl":
                        field_name = struct_elem_decl.children.value # IDENTIFIER
                        field_type_node = struct_elem_decl.children # type_specifier
                        fields[field_name] = self._resolve_type_specifier(field_type_node)
            return StructType("ANON_STRUCT_DEF", fields) # Anonymous struct def
        return ElementaryType("UNKNOWN_COMPLEX_TYPE")


    @v_args(tree=True)
    def program_declaration(self, tree):
        prog_name_token = tree.children
        prog_name = prog_name_token.value
        self.st.global_scope.add_symbol(Symbol(prog_name, PouType(prog_name, "PROGRAM"), 'program', location=prog_name_token))
        self.st.enter_scope(f"PROGRAM_{prog_name}")
        self.visit_children(tree)
        self.st.exit_scope()

    @v_args(tree=True)
    def function_block_declaration(self, tree):
        fb_name_token = tree.children
        fb_name = fb_name_token.value
        # FB can be used as a type
        fb_type_obj = PouType(fb_name, "FUNCTION_BLOCK")
        self.st.global_scope.add_symbol(Symbol(fb_name, fb_type_obj, 'fb_type', location=fb_name_token))
        self.st.enter_scope(f"FB_{fb_name}")
        # Add 'THIS' pointer implicitly? For now, no.
        self.visit_children(tree)
        self.st.exit_scope()

    @v_args(tree=True)
    def function_declaration(self, tree):
        func_name_token = tree.children
        func_name = func_name_token.value
        return_type_node = tree.children # type_specifier
        return_type = self._resolve_type_specifier(return_type_node)
        self.st.global_scope.add_symbol(Symbol(func_name, PouType(func_name, "FUNCTION", return_type=return_type), 'function', location=func_name_token))
        self.st.enter_scope(f"FUNCTION_{func_name}")
        # Parameters will be handled by var_block within the function's scope
        self.visit_children(tree)
        self.st.exit_scope()

    @v_args(tree=True)
    def var_decl_item(self, tree):
        # var_decl_item : identifier_list COLON type_specifier?
        id_list_node = tree.children
        type_spec_node = tree.children
        resolved_type = self._resolve_type_specifier(type_spec_node)

        for id_token in id_list_node.children:
            var_name = id_token.value
            # Determine var_kind from parent var_block (VAR_INPUT_KW etc.)
            # For simplicity, assume 'variable' kind
            var_kind = "variable" # This needs to be derived from var_qualifier_block
            parent_var_block = tree # This needs to search upwards, or pass context down.
            # Simplified: Assume current scope is POU, so it's a local var or param
            self.st.current_scope.add_symbol(Symbol(var_name, resolved_type, var_kind, location=id_token))

    @v_args(tree=True)
    def type_declaration(self, tree):
        # type_declaration : IDENTIFIER COLON type_specifier
        type_name_token = tree.children
        type_name = type_name_token.value
        type_spec_node = tree.children
        actual_type = self._resolve_type_specifier(type_spec_node)
        # If actual_type is a StructType and was anonymous, update its name
        if isinstance(actual_type, StructType) and actual_type.name == "ANON_STRUCT_DEF":
            actual_type.name = type_name # Give the struct its declared name

        self.st.global_scope.add_symbol(Symbol(type_name, actual_type, 'type', location=type_name_token))

@v_args(meta=True) # Provides meta (line/col info)
class TypeAnnotator(Transformer):
    def __init__(self, symbol_table):
        self.st = symbol_table
        super().__init__()

    def _get_node_type(self, node):
        return getattr(node, 'st_type', ElementaryType("UNKNOWN"))

    # --- Literal Handling ---
    def typed_integer_literal(self, items, meta):
        # (SINT_KW | INT_KW...) HASH SIGNED_NUMBER
        type_kw_token = items.children # e.g. INT_KW token
        type_name = type_kw_token.type.replace("_KW", "")
        # value_token = items # SIGNED_NUMBER
        # actual_value = int(value_token.value)
        tree = Tree("typed_literal", items, meta=meta)
        tree.st_type = ElementaryType(type_name)
        return tree

    def integer_or_real_literal(self, items, meta):
        # SIGNED_NUMBER
        value_str = items.value
        tree = Tree("literal_value", items, meta=meta)
        if '.' in value_str or 'e' in value_str.lower():
            tree.st_type = ElementaryType("REAL") # Default untyped float to REAL
        else:
            tree.st_type = ElementaryType("INT") # Default untyped int to INT
        return tree

    def boolean_literal(self, items, meta):
        tree = Tree("literal_value", items, meta=meta)
        tree.st_type = ElementaryType("BOOL")
        return tree

    def string_literal(self, items, meta):
        tree = Tree("literal_value", items, meta=meta)
        tree.st_type = ElementaryType("STRING") # Could be WSTRING based on quotes if grammar distinguishes
        return tree

    # --- Variable and Expression Handling ---
    @v_args(inline=True) # Children passed as direct arguments
    def variable_access(self, identifier_token, *accessors, meta):
        # IDENTIFIER (array_accessor | struct_member_accessor)*
        var_name = identifier_token.value
        current_type_sym = self.st.current_scope.lookup_symbol(var_name)

        if not current_type_sym:
            # Variable not found, assign UNKNOWN type
            tree = Tree("variable_access", [identifier_token] + list(accessors), meta=meta)
            tree.st_type = ElementaryType("UNKNOWN_VAR_" + var_name)
            return tree

        current_type = current_type_sym.type # This is an StDataType object

        for acc in accessors: # acc is a Tree for array_accessor or struct_member_accessor
            if not isinstance(current_type, StDataType): # Should not happen if types are objects
                 current_type = ElementaryType("ERROR_PREV_ACCESS")
                 break
            if acc.data == "array_accessor":
                if isinstance(current_type, ArrayType):
                    # Type check indices in acc.children (expression_list)
                    # For now, assume indices are valid
                    current_type = current_type.element_type
                else:
                    current_type = ElementaryType("NOT_AN_ARRAY")
                    break
            elif acc.data == "struct_member_accessor":
                if isinstance(current_type, StructType):
                    member_name = acc.children.value # IDENTIFIER token
                    current_type = current_type.fields.get(member_name, ElementaryType("UNKNOWN_MEMBER"))
                elif isinstance(current_type, PouType) and current_type.pou_kind == "FUNCTION_BLOCK":
                    # Accessing output of an FB instance. This needs full FB type info.
                    # fb_type_sym = self.st.global_scope.lookup_symbol(current_type.name)
                    # if fb_type_sym and isinstance(fb_type_sym.type, StructType): # FB outputs as fields
                    #    member_name = acc.children.value
                    #    current_type = fb_type_sym.type.fields.get(member_name, ElementaryType("UNKNOWN_FB_OUTPUT"))
                    # else:
                    current_type = ElementaryType("FB_MEMBER_ACCESS_UNSUPPORTED") # Simplified
                    break
                else:
                    current_type = ElementaryType("NOT_A_STRUCT_OR_FB")
                    break
        
        # Create a new Tree for variable_access and attach the final type
        # The children of variable_access in the original tree are IDENTIFIER and accessors
        # We need to ensure these children are also transformed if they contain expressions (e.g., array index)
        # Lark's Transformer processes children first. So 'identifier_token' might be a Token,
        # and 'accessors' might be already transformed Trees.
        
        # Reconstruct the tree with potentially transformed children
        transformed_children = [identifier_token] # Assuming identifier_token is not transformed further by itself
        for acc_node in accessors:
            transformed_children.append(acc_node) # acc_node is already a transformed Tree

        tree = Tree("variable_access", transformed_children, meta=meta)
        tree.st_type = current_type
        return tree


    def primary_expression(self, children, meta):
        # literal | variable_access | function_call | LPAREN expression RPAREN
        # Children are already transformed. The child (single) is the item.
        child_node = children
        # The type of primary_expression is the type of its child.
        # Re-wrap to allow attaching type to primary_expression itself if needed,
        # or just pass child_node up if primary_expression is inlined by '?'
        # For explicit node:
        tree = Tree("primary_expression", children, meta=meta)
        tree.st_type = self._get_node_type(child_node)
        return tree

    def add_expression(self, children, meta):
        # term ( (ADD | SUB) term )*
        # Children are [term_node, op_token, term_node, op_token,...]
        # The first child is the initial term
        current_type = self._get_node_type(children)

        for i in range(1, len(children), 2):
            # op = children[i] # Token for ADD or SUB
            right_operand_type = self._get_node_type(children[i+1])
            # Simple type promotion: if either is REAL, result is REAL.
            # Otherwise, if both INT-like, result is INT-like.
            # This is a simplification. IEC61131-3 is strict about no implicit conversions.
            if current_type == ElementaryType("REAL") or right_operand_type == ElementaryType("REAL"):
                current_type = ElementaryType("REAL")
            elif current_type.name.endswith("INT") and right_operand_type.name.endswith("INT"): # crude check
                # Determine largest int type if needed, for now, stick to INT/DINT etc.
                # For simplicity, assume they result in a compatible integer type or DINT
                current_type = ElementaryType("DINT") # Default for mixed int ops
            else: # Type mismatch or non-numeric
                current_type = ElementaryType("TYPE_ERROR_IN_ADD")
                break
        
        tree = Tree("add_expression_typed", children, meta=meta)
        tree.st_type = current_type
        return tree
    
    # Similar methods for mul_expression, comparison_expression, logical_expressions etc.
    # Each would implement its specific type logic.

    def function_call(self, children, meta):
        # IDENTIFIER LPAREN [param_assignment_list]? RPAREN
        func_name_token = children
        func_name = func_name_token.value
        
        func_sym = self.st.current_scope.lookup_symbol(func_name) # Or global for std functions
        return_type = ElementaryType(f"UNKNOWN_FUNC_RET_{func_name}")

        if func_sym and (func_sym.kind == 'function' or (isinstance(func_sym.type, PouType) and func_sym.type.pou_kind == "FUNCTION")) :
            if isinstance(func_sym.type, PouType) and func_sym.type.return_type:
                 return_type = func_sym.type.return_type
            # Parameter type checking would occur here by inspecting children (param_assignment_list)
            # and comparing with func_sym.type.params
        
        tree = Tree("function_call_typed", children, meta=meta)
        tree.st_type = return_type
        return tree

    def assignment_statement(self, children, meta):
        # variable_access ASSIGN expression
        # Children are already transformed
        lhs_node = children # variable_access node with.st_type
        rhs_node = children # expression node with.st_type

        lhs_type = self._get_node_type(lhs_node)
        rhs_type = self._get_node_type(rhs_node)

        # Perform type compatibility check here if needed.
        # For "no error handling", we just note the types.
        # The assignment itself doesn't have a "type" in the same way an expression does.
        # We can annotate the assignment statement with this info if desired.
        tree = Tree("assignment_statement_typed", children, meta=meta)
        setattr(tree, 'lhs_type', lhs_type)
        setattr(tree, 'rhs_type', rhs_type)
        # An assignment statement itself doesn't have a type, so no tree.st_type
        return tree

    def __default__(self, data, children, meta):
        # Default behavior for rules not explicitly handled:
        # Create a new tree, try to infer type from first child if sensible
        new_tree = Tree(data, children, meta)
        if children and hasattr(children, 'st_type'):
            # Tentatively assign type of first child if rule is a simple wrapper
            # This is a heuristic and might not always be correct.
            # Specific rules should handle their types explicitly.
            # setattr(new_tree, 'st_type', children.st_type)
            pass # Better to be explicit for each rule
        return new_tree

# Global store for the final annotated AST
annotated_ast_global = None

def get_node_type(node):
    global annotated_ast_global
    if not annotated_ast_global:
        return "AST not processed yet" # Or raise error

    # This function would ideally search the specific node within the annotated_ast_global
    # For simplicity, we assume 'node' itself is already an annotated node from the Transformer.
    if hasattr(node, 'st_type'):
        return node.st_type
    elif isinstance(node, Token):
        # Try to infer type for simple tokens if not wrapped by a rule that adds.st_type
        if node.type == "IDENTIFIER":
            # This needs context from symbol table, which get_node_type might not have directly
            # This indicates IDENTIFIERs should always be processed by a rule like 'variable_access'
            return ElementaryType("AMBIGUOUS_IDENTIFIER_TYPE")
        # Other tokens (keywords, operators) don't have ST data types themselves
        return ElementaryType("TOKEN_HAS_NO_ST_TYPE")
    return ElementaryType("UNKNOWN_NODE_OR_TYPE_NOT_SET")


st_code_example = """
PROGRAM Main
    VAR
        myInt : INT;
        myReal : REAL;
        myBool : BOOL;
        myArr : ARRAY [1..3] OF INT;
    END_VAR

    myReal := myInt + 20.5; // Type promotion/conversion might be an issue
    myBool := myInt > 5;
    myArr := myInt;
    // CheckNode := myArr[myInt]; // Index is INT, value is INT
END_PROGRAM
"""

def main_parser_flow(code_to_parse):
    global annotated_ast_global

    # 1. Parse the ST code
    raw_ast = st_parser.parse(code_to_parse)
    # print("Raw AST:\n", raw_ast.pretty())

    # 2. Build Symbol Table
    symbol_table_instance = SymbolTable()
    symbol_builder = SymbolTableBuilder(symbol_table_instance)
    symbol_builder.visit(raw_ast) # Populate symbol_table_instance

    # print("\nSymbol Table:")
    # scope = symbol_table_instance.global_scope
    # while scope:
    #     print(scope)
    #     if scope.symbols:
    #         for s_name, s_obj in scope.symbols.items():
    #             print(f"  - {s_obj}")
    #     # This doesn't show nested scopes correctly, need proper traversal
    #     # For now, just print global and current (which will be last POU's scope)
    #     if scope == symbol_table_instance.global_scope:
    #         prog_scope_name = "PROGRAM_Main" # Hardcoded for example
    #         prog_scope = next((s for s_child in symbol_table_instance.global_scope.symbols.values() if hasattr(s_child, 'name') and s_child.name == prog_scope_name), None)

    #     scope = None # End loop for simple print


    # 3. Annotate AST with Types
    type_annotator = TypeAnnotator(symbol_table_instance)
    annotated_ast = type_annotator.transform(raw_ast)
    annotated_ast_global = annotated_ast # Store for get_node_type

    # print("\nAnnotated AST:\n", annotated_ast.pretty())

    # 4. Demonstrate get_node_type
    # This requires finding specific nodes in the annotated_ast.
    # Example: Find the node for 'myInt' in 'myReal := myInt + 20.5;'
    # This is non-trivial without node IDs or more complex traversal.
    # For demonstration, let's assume we can pick a node.
    # We'll iterate and find a node we are interested in.
    
    # Example: Find the 'myInt' variable access node in an assignment
    assignment_node = None
    for pou in annotated_ast.children: # Assuming start rule produces list of POUs
        if pou.data == "program_declaration":
            stmt_list = pou.children[-2] # Heuristic: statement_list before END_PROGRAM_KW
            if stmt_list and stmt_list.data == "statement_list":
                for stmt in stmt_list.children:
                    if isinstance(stmt, Tree) and stmt.data == "assignment_statement_typed":
                        # myReal := myInt + 20.5;
                        # lhs is variable_access for myReal
                        # rhs is add_expression for myInt + 20.5
                        # We want to find 'myInt' inside the add_expression
                        rhs_expr = stmt.children # add_expression_typed
                        if rhs_expr.data == "add_expression_typed":
                            # children are [term_node, op_token, term_node]
                            # first term_node -> power_expr -> unary_expr -> primary_expr -> variable_access for myInt
                            term1 = rhs_expr.children # This is already a transformed node
                            # Need to traverse down to find the variable_access for 'myInt'
                            # This recursive search is for demonstration.
                            
                            def find_var_access_node(node, var_name):
                                if isinstance(node, Tree):
                                    if node.data == "variable_access" and \
                                       isinstance(node.children, Token) and \
                                       node.children.value == var_name:
                                        return node
                                    for child in node.children:
                                        found = find_var_access_node(child, var_name)
                                        if found: return found
                                return None

                            my_int_node_in_expr = find_var_access_node(term1, "myInt")
                            if my_int_node_in_expr:
                                print(f"\nType of 'myInt' in expression '{my_int_node_in_expr.children.value}': {get_node_type(my_int_node_in_expr)}")
                            
                            my_real_literal_node = find_var_access_node(rhs_expr.children, None) # Find a literal
                            # This search is too naive for literals. Let's assume we found it.
                            # Example: if rhs_expr.children was a literal node from transformer
                            # print(f"Type of literal '20.5': {get_node_type(some_literal_node_for_20_5)}")
                            break # Found one assignment

    # Example: Get type of the assignment expression itself (rhs_node of myReal assignment)
    # (Assuming we have 'assignment_node' from a more robust search)
    # if assignment_node and len(assignment_node.children) > 2:
    #    rhs_expression_node = assignment_node.children
    #    print(f"Type of expression 'myInt + 20.5': {get_node_type(rhs_expression_node)}")


if __name__ == '__main__':
    main_parser_flow(st_code_example)