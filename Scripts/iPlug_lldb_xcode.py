import lldb
import re

# USAGE
#
# Put this line in your ~/.lldbinit file:
#
#  command script import [path]
#
# Where [path] is the full path to this file. For example:
#
#  command script import /Users/me/juce-toys/juce_lldb_xcode.py

def __lldb_init_module(debugger, dict):

    debugger.HandleCommand('type summary add WDL_String -F iPlug_lldb_xcode.string_summary')

    debugger.HandleCommand('type summary add --inline-children IRECT')
    debugger.HandleCommand('type summary add --inline-children IColor')
    debugger.HandleCommand('type summary add --inline-children IBlend')

    debugger.HandleCommand('type synthetic add WDL_TypedBuf<.*> -x -l iPlug_lldb_xcode.WDL_TypedBufChildrenProvider')

    debugger.HandleCommand('type synthetic add WDL_PtrList<.*> -x -l iPlug_lldb_xcode.WDL_PtrListChildrenProvider')

def string_summary(valueObject, dictionary):
    debugger = lldb.debugger
    target = debugger.GetSelectedTarget()
    char_ptr = target.FindFirstType("char").GetPointerType()
    s = valueObject.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_buf').Cast(char_ptr).GetSummary()
    return s

class WDL_TypedBufChildrenProvider:
    def __init__(self, valobj, internal_dict):
        typename = valobj.GetTypeName()
        base_type = re.match('WDL_TypedBuf<(.*)>', typename, re.S).group(1)
        debugger = lldb.debugger
        target = debugger.GetSelectedTarget()
        self.data_type = target.FindFirstType(base_type)
        self.valobj = valobj

    def num_children(self):
        try:
            buf = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_buf').GetValueAsUnsigned(0)
            size = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_size').GetValueAsUnsigned(0)
            data_size = self.data_type.GetByteSize();
            alloc = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_alloc').GetValueAsUnsigned(0)

            # Make sure nothing is NULL
            if buf == 0 or alloc == 0:
                return 0

            if (size % data_size) != 0:
                return 0
            else:
                num_children = size / data_size
            return num_children
        except:
            return 0

    def get_child_index(self,name):
        try:
            return int(name.lstrip('[').rstrip(']'))
        except:
            return -1

    def get_child_at_index(self,index):
        if index < 0:
            return None
        if index >= self.num_children():
            return None
        try:
            offset = index * self.data_type.GetByteSize()
            buf = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_buf').GetValueAsUnsigned()
            return self.valobj.CreateValueFromAddress('[' + str(index) + ']', buf + offset, self.data_type)
        except:
            return None

    def update(self):
        pass
        #this call should be used to update the internal state of this Python object whenever the state of the variables in LLDB changes.[1]

    def has_children(self):
        return True

class WDL_PtrListChildrenProvider:
    def __init__(self, valobj, internal_dict):
        typename = valobj.GetTypeName()
        base_type = re.match('WDL_PtrList<(.*)>', typename, re.S).group(1)
        debugger = lldb.debugger
        target = debugger.GetSelectedTarget()
        self.data_type = target.FindFirstType(base_type)
        self.valobj = valobj

    def num_children(self):
        try:
            buf = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_buf').GetValueAsUnsigned(0)
            size = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_size').GetValueAsUnsigned(0)
            data_size = self.data_type.GetPointerType().GetByteSize();
            alloc = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_alloc').GetValueAsUnsigned(0)

            # Make sure nothing is NULL
            if buf == 0 or alloc == 0:
                return 0

            if (size % data_size) != 0:
                return 0
            else:
                num_children = size / data_size
            return num_children
        except:
            return 0

    def get_child_index(self,name):
        try:
            return int(name.lstrip('[').rstrip(']'))
        except:
            return -1

    def get_child_at_index(self,index):
        if index < 0:
            return None
        if index >= self.num_children():
            return None
        try:
            offset = index * self.data_type.GetPointerType().GetByteSize()
            buf = self.valobj.GetChildMemberWithName('m_hb').GetChildMemberWithName('m_buf').GetValueAsUnsigned()
            return self.valobj.CreateValueFromAddress('[' + str(index) + ']', buf + offset, self.data_type.GetPointerType())
        except:
            return None

    def update(self):
        pass
        #this call should be used to update the internal state of this Python object whenever the state of the variables in LLDB changes.[1]

    def has_children(self):
        return True
