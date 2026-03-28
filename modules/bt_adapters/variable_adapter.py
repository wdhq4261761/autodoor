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
        self.variable_name = self.config.get("variable_name", "")
        self.operator = self.config.get("operator", "==")
        self.compare_value = self.config.get("compare_value")
    
    def tick(self, context: "ExecutionContext") -> NodeStatus:
        """
        执行变量条件检测
        
        Args:
            context: 执行上下文
            
        Returns:
            检测结果状态
        """
        if not self.enabled:
            return NodeStatus.SUCCESS
        
        if not context.check_running():
            return NodeStatus.ABORTED
        
        if not self.variable_name:
            context.log(f"变量条件节点 {self.name}: 未配置变量名")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
        
        try:
            actual_value = context.blackboard.get(self.variable_name)
            
            if self.operator not in self.OPERATORS:
                context.log(f"变量条件节点 {self.name}: 未知的运算符 {self.operator}")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
            
            compare_func = self.OPERATORS[self.operator]
            result = compare_func(actual_value, self.compare_value)
            
            if result:
                context.log(f"变量条件节点 {self.name}: {self.variable_name} {self.operator} {self.compare_value} -> 满足")
                self._status = NodeStatus.SUCCESS
                return NodeStatus.SUCCESS
            else:
                context.log(f"变量条件节点 {self.name}: {self.variable_name} {self.operator} {self.compare_value} -> 不满足 (实际值: {actual_value})")
                self._status = NodeStatus.FAILURE
                return NodeStatus.FAILURE
                
        except Exception as e:
            context.log(f"变量条件节点 {self.name}: 执行出错 - {e}")
            self._status = NodeStatus.FAILURE
            return NodeStatus.FAILURE
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data["config"] = {
            **self.config,
            "variable_name": self.variable_name,
            "operator": self.operator,
            "compare_value": self.compare_value,
        }
        return data
