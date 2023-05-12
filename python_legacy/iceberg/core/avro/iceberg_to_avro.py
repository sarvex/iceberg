# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

from iceberg.api.types import BinaryType, TypeID


class IcebergToAvro(object):

    @staticmethod
    def type_to_schema(struct_type, name):
        struct_fields = [
            {
                "field-id": field.id,
                "name": field.name,
                "type": IcebergToAvro.get_field(field),
            }
            for field in struct_type.fields
        ]
        return {"type": "record",
                "name": name,
                "fields": struct_fields}

    @staticmethod
    def get_field(field):
        if field.type.is_primitive_type():
            return IcebergToAvro.to_option(field)

        elif field.type.type_id == TypeID.STRUCT:
            struct_fields = []
            for struct_field in field.type.fields:
                field_dict = {"field-id": struct_field.id,
                              "name": struct_field.name,
                              "type": IcebergToAvro.get_field(struct_field)}
                if struct_field.is_optional:
                    field_dict["default"] = None

                struct_fields.append(field_dict)

            return {"fields": struct_fields,
                    "name": field.name,
                    "type": "record"}

        elif field.type.type_id == TypeID.LIST:
            array_obj = {'element-id': field.type.element_id,
                         "items": IcebergToAvro.get_field(field.type.element_field),
                         "type": 'array'}
            return ['null', array_obj] if field.is_optional else array_obj
        elif field.type.type_id == TypeID.MAP:
            key = field.type.key_field
            value = field.type.value_field
            array_obj = {
                "items": {
                    "fields": [
                        {
                            "field-id": key.field_id,
                            "name": key.name,
                            "type": IcebergToAvro.get_field(key),
                        },
                        {
                            "field-id": value.field_id,
                            "name": value.name,
                            "type": IcebergToAvro.get_field(value),
                        },
                    ],
                    "name": f"k{key.field_id}_v{value.field_id}",
                    "type": "record",
                },
                "logicalType": "map",
                "type": "array",
            }
            return ["null", array_obj] if field.is_optional else array_obj

    @staticmethod
    def to_option(field):
        type_name = "bytes" if field.type == BinaryType.get() else str(field.type)
        return ["null", type_name] if field.is_optional else type_name
