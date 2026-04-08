"""
变量条件节点适配器

检测黑板变量是否满足指定条件
"""

from typing import Any, Dict, Optional, TYPE_CHECKING

from modules.behavior_tree.nodes import ConditionNode, NodeStatus

if TYPE_CHECKING:
    from modules.behavior_tree.context import ExecutionContext


class VariableConditionNode(ConditionNode):
    """
    变量条件节点
    
    检测黑板变量是否满足指定条件
    支持比较运算符: ==, !=, >, <, >=, <=
    """
    
    OPERATORS = {
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
        ">": lambda a, b: a > b if a is not None and b is not None else False,
        "<": lambda a, b: a < b if a is not None and b is not None else False,
        ">=": lambda a, b: a >= b if a is not None and b is not None else False,
        "<=": lambda a, b: a <= b if a is not None and b is not None else False,
        "exists": lambda a, b: a is not None,
        "not_exists": lambda a, b: a is None,
        "contains": lambda a, b: b in a if a is not None and isinstance(a, (str, list, dict)) else False,
        "not_contains": lambda a, b: b not in a if a is not None and isinstance(a, (str, list, dict)) else True,
    }
    
    def __init__(self, node_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(node_id, config)
    
    def _execute_condition(self, context: "ExecutionContext") -> NodeStatus:
        variable_name = self.config.get("variable_name", "")
        operator = self.config.get("operator", "==")
        compare_value = self.config.get("compare_value")
        
        if not variable_name:
            context.log(f"变量条件节点 {self.name}: 未配置变量名")
            return NodeStatus.FAILURE
        
        try:
            actual_value = context.blackboard.get(variable_name)
            
            if operator not in self.OPERATORS:
                context.log(f"变量条件节点 {self.name}: 未知的运算符 {operator}")
                return NodeStatus.FAILURE
            
            compare_value_typed = self._convert_compare_value(actual_value, compare_value, operator)
            
            compare_func = self.OPERATORS[operator]
            result = compare_func(actual_value, compare_value_typed)
            
            if result:
                context.log(f"变量条件节点 {self.name}: {variable_name} {operator} {compare_value_typed} -> 满足")
                return NodeStatus.SUCCESS
            else:
                context.log(f"变量条件节点 {self.name}: {variable_name} {operator} {compare_value_typed} -> 不满足 (实际值: {actual_value})")
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"变量条件节点 {self.name}: 执行出错 - {e}")
            return NodeStatus.FAILURE
    
    def _convert_compare_value(self, actual_value, compare_value, operator: str):
        """
        根据实际值类型转换比较值
        
        当实际值为数字时，尝试将比较值转换为相同类型
        当实际值为字符串时，保持比较值为字符串
        """
        if operator in ("exists", "not_exists"):
            return compare_value
        
        if actual_value is None:
            return compare_value
        
        if isinstance(actual_value, bool):
            if isinstance(compare_value, str):
                if compare_value.lower() in ("true", "1", "yes"):
                    return True
                elif compare_value.lower() in ("false", "0", "no"):
                    return False
            return compare_value
        
        if isinstance(actual_value, (int, float)):
            if isinstance(compare_value, str):
                try:
                    if "." in compare_value:
                        return float(compare_value)
                    else:
                        return int(compare_value)
                except (ValueError, TypeError):
                    pass
            return compare_value
        
        return compare_value
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "variable_name": self.config.get("variable_name", ""),
            "operator": self.config.get("operator", "=="),
            "compare_value": self.config.get("compare_value"),
        }
        return data
